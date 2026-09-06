import time
import math
import config


class ObjectTracker:
    """
    Tracks bags across frames and determines
    LOW / UNCERTAIN / HIGH threat levels.

    Handles any number of bags at once (each gets its own entry in
    `self.tracked`, keyed by its own id) - this already runs on every
    bag detected in a frame, not just one, so multi-bag / CCTV-style
    scanning is inherent in this loop, not something extra to build.

    A bag is also kept "alive" and drawn at its last known position
    for a short grace period even on frames where YOLO's confidence
    for it dips and it isn't returned - that's what stops the box
    from flickering off and on when the bag hasn't actually moved.
    """

    def __init__(self, debug=None):
        self.tracked = {}
        self.next_id = 0
        self.debug = config.DEBUG if debug is None else debug

    def _match_or_create(self, centroid, now):

        best_id = None
        best_dist = config.MATCH_DISTANCE_PX

        for obj_id, data in self.tracked.items():

            dist = math.hypot(
                centroid[0] - data["centroid"][0],
                centroid[1] - data["centroid"][1]
            )

            if dist < best_dist:
                best_dist = dist
                best_id = obj_id

        if best_id is None:

            best_id = self.next_id
            self.next_id += 1

            self.tracked[best_id] = {
                "centroid": centroid,
                "first_seen": now,
                "last_person_nearby": now,
                "last_seen": now,
            }

        return best_id

    @staticmethod
    def _smooth(old_val, new_val, alpha=0.6):
        """
        Exponential moving average so the box eases toward the new
        position instead of snapping - this removes most of the
        pixel-to-pixel jitter that makes a static box look "alive".
        """
        return tuple(
            int(o + (n - o) * alpha)
            for o, n in zip(old_val, new_val)
        )

    def update(self, detections):

        now = time.time()

        persons = [
            d["centroid"]
            for d in detections
            if d["class_name"] == "person"
        ]

        bag_classes = (
            "backpack",
            "handbag",
            "suitcase"
        )

        bags = [
            d
            for d in detections
            if d["class_name"] in bag_classes
        ]

        seen_ids = set()

        # ------------------------------------------------------
        # Update every bag that WAS detected this frame.
        # ------------------------------------------------------

        for bag in bags:

            obj_id = self._match_or_create(
                bag["centroid"],
                now
            )

            state = self.tracked[obj_id]

            if "bbox" in state:
                state["bbox"] = self._smooth(
                    state["bbox"], bag["bbox"]
                )
                state["centroid"] = self._smooth(
                    state["centroid"], bag["centroid"]
                )
            else:
                state["bbox"] = bag["bbox"]
                state["centroid"] = bag["centroid"]

            state["class_name"] = bag["class_name"]
            state["confidence"] = bag["confidence"]
            state["last_seen"] = now
            state["missing"] = False

            person_nearby = any(
                math.hypot(
                    bag["centroid"][0] - person[0],
                    bag["centroid"][1] - person[1]
                ) < config.PERSON_PROXIMITY_PX
                for person in persons
            )

            if person_nearby:
                state["last_person_nearby"] = now

            seen_ids.add(obj_id)

        # ------------------------------------------------------
        # Carry forward bags that existed before but were missed
        # this frame, as long as they're still inside the grace
        # window. This is what prevents the flicker: we keep
        # drawing at the last known spot instead of dropping the
        # box the instant one frame's confidence dips.
        # ------------------------------------------------------

        for obj_id, state in self.tracked.items():

            if obj_id in seen_ids:
                continue

            if "bbox" not in state:
                continue

            missed_for = now - state["last_seen"]

            if missed_for <= config.TRACK_GRACE_SEC:
                state["missing"] = True
                seen_ids.add(obj_id)

        # ------------------------------------------------------
        # Build results for every track that's still considered
        # "visible" this frame (freshly detected or in grace period).
        # ------------------------------------------------------

        results = []

        for obj_id in seen_ids:

            state = self.tracked[obj_id]

            unattended_for = (
                now - state["last_person_nearby"]
            )

            if unattended_for < config.UNCERTAIN_AFTER_SEC:

                level = "LOW"

            elif unattended_for < config.HIGH_ALERT_AFTER_SEC:

                level = "UNCERTAIN"

            else:

                level = "HIGH"

            results.append({
                "class_name": state["class_name"],
                "confidence": state["confidence"],
                "bbox": state["bbox"],
                "centroid": state["centroid"],
                "object_id": obj_id,
                "threat_level": level,
                "unattended_seconds": round(
                    unattended_for,
                    1
                ),
                "predicted": state.get("missing", False),
            })

            if self.debug:
                tag = " (predicted/grace)" if state.get("missing") else ""
                print(
                    f"[TRACKER] track_id={obj_id} "
                    f"class={state['class_name']}{tag}"
                )
                print(
                    f"[THREAT] {state['class_name']} (id={obj_id}) "
                    f"unattended for {unattended_for:.1f}s -> {level}"
                )

        # ------------------------------------------------------
        # Only fully forget a track after TRACK_FORGET_SEC with
        # zero detections - this frees the id for reuse once the
        # bag is genuinely gone (picked up, left frame, etc.).
        # ------------------------------------------------------

        for obj_id in list(self.tracked):

            if (
                now - self.tracked[obj_id]["last_seen"]
                > config.TRACK_FORGET_SEC
            ):
                del self.tracked[obj_id]

        return results