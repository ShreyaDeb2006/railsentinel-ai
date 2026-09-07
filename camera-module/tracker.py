import time
import math
from collections import deque, Counter

import config


def _iou(box_a, box_b):
    """Standard intersection-over-union between two (x1,y1,x2,y2) boxes."""

    xa = max(box_a[0], box_b[0])
    ya = max(box_a[1], box_b[1])
    xb = min(box_a[2], box_b[2])
    yb = min(box_a[3], box_b[3])

    inter_w = max(0, xb - xa)
    inter_h = max(0, yb - ya)
    inter_area = inter_w * inter_h

    area_a = (box_a[2] - box_a[0]) * (box_a[3] - box_a[1])
    area_b = (box_b[2] - box_b[0]) * (box_b[3] - box_b[1])

    union = area_a + area_b - inter_area

    return inter_area / union if union > 0 else 0.0


def _centroid_distance(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


class ObjectTracker:
    """
    Tracks PEOPLE and BAGS as two independent, persistent registries,
    and separately decides bag ATTENDED/UNATTENDED status by checking
    bag-person association every frame - not just on frames where the
    bag itself happens to be freshly (re)detected.

    Why two registries instead of one:

    A single physical bag can flicker between being labeled "suitcase"
    one frame and "person" the next (YOLOv8n genuinely confuses some
    held/handled bag shapes with people). If association is only
    checked on frames where BOTH a person AND a bag are detected
    SIMULTANEOUSLY, it almost never fires for exactly this case -
    because the model is alternating which single label it gives the
    same object, not outputting both at once. That was the root cause
    of bags going HIGH while being actively held: the code only ever
    looked for a nearby person on frames where the bag itself was also
    freshly redetected, so a frame with ONLY "person" output (the
    bag's own moment of being mislabeled) never got compared against
    the bag's position at all.

    The fix: track persons with their own grace period (same idea as
    bags already had), and check bag-person association against
    CURRENTLY ACTIVE persons every single frame, whether or not the
    bag was freshly redetected that frame.

    A person also needs to be "confirmed" (existed for
    PERSON_CONFIRM_SEC, tolerating brief grace gaps) before their
    presence fully resets a bag's unattended timer. A single-frame,
    unconfirmed person nearby still counts as WEAK evidence - it caps
    the threat level at UNCERTAIN instead of letting it jump to HIGH,
    without fully resetting the clock on a single flicker either. This
    is what makes single-frame confidence noise around the acceptance
    threshold (Failure 4 in testing) a non-issue: a track survives the
    dip via the grace period, and neither a momentary appearance nor a
    momentary disappearance flips the attended state outright.

    NOTE on person/bag box overlap: overlap is used ONLY as ASSOCIATION
    evidence (this bag is probably being held). It is never used to
    delete or suppress either detection. An earlier version of this
    file dropped the "person" box whenever it overlapped a bag box
    above a threshold, reasoning that meant the model was
    double-labeling one object - but a real person carrying a real bag
    also produces heavy overlap, and that rule would incorrectly
    delete genuine person detections during completely normal carrying.
    Both boxes are always kept; overlap just feeds the association
    decision.
    """

    def __init__(self, debug=None):

        self.persons = {}
        self.bags = {}

        self.next_person_id = 0
        self.next_bag_id = 0

        self.debug = config.DEBUG if debug is None else debug

        self._active_persons_cache = []

    # ------------------------------------------------------------
    # Generic nearest-centroid matching, shared by both registries.
    # ------------------------------------------------------------

    @staticmethod
    def _match(registry, centroid):

        best_id = None
        best_dist = config.MATCH_DISTANCE_PX

        for obj_id, state in registry.items():

            dist = _centroid_distance(centroid, state["centroid"])

            if dist < best_dist:
                best_dist = dist
                best_id = obj_id

        return best_id

    @staticmethod
    def _smooth(old_val, new_val, alpha=0.6):
        """Exponential moving average - eases toward the new position
        instead of snapping, removing most pixel-to-pixel jitter."""
        return tuple(
            int(o + (n - o) * alpha)
            for o, n in zip(old_val, new_val)
        )

    # ------------------------------------------------------------
    # PERSON tracking
    # ------------------------------------------------------------

    def _update_persons(self, raw_persons, now):

        seen_ids = set()

        for p in raw_persons:

            pid = self._match(self.persons, p["centroid"])

            if pid is None:

                pid = self.next_person_id
                self.next_person_id += 1

                self.persons[pid] = {
                    "bbox": p["bbox"],
                    "centroid": p["centroid"],
                    "confidence": p["confidence"],
                    "first_seen": now,
                    "last_seen": now,
                    "missing": False,
                }

            else:

                state = self.persons[pid]
                state["bbox"] = self._smooth(state["bbox"], p["bbox"])
                state["centroid"] = self._smooth(
                    state["centroid"], p["centroid"]
                )
                state["confidence"] = p["confidence"]
                state["last_seen"] = now
                state["missing"] = False

            seen_ids.add(pid)

        # Grace-period carry-forward, same idea as bags.
        for pid, state in self.persons.items():

            if pid in seen_ids:
                continue

            if now - state["last_seen"] <= config.TRACK_GRACE_SEC:
                state["missing"] = True
                seen_ids.add(pid)

        # Fully forget long-gone persons.
        for pid in list(self.persons):
            if (
                now - self.persons[pid]["last_seen"]
                > config.TRACK_FORGET_SEC
            ):
                del self.persons[pid]

        active = []

        for pid in seen_ids:

            state = self.persons[pid]

            confirmed = (
                now - state["first_seen"]
            ) >= config.PERSON_CONFIRM_SEC

            active.append({
                "person_id": pid,
                "bbox": state["bbox"],
                "centroid": state["centroid"],
                "confidence": state["confidence"],
                "confirmed": confirmed,
                "predicted": state.get("missing", False),
            })

        return active

    # ------------------------------------------------------------
    # BAG tracking + attended/unattended association
    # ------------------------------------------------------------

    def _update_bags(self, raw_bags, now, active_persons):

        seen_ids = set()

        for b in raw_bags:

            bid = self._match(self.bags, b["centroid"])

            if bid is None:

                bid = self.next_bag_id
                self.next_bag_id += 1

                self.bags[bid] = {
                    "bbox": b["bbox"],
                    "centroid": b["centroid"],
                    "confidence": b["confidence"],
                    "class_history": deque(
                        maxlen=config.BAG_CLASS_HISTORY_LEN
                    ),
                    "first_seen": now,
                    "last_seen": now,
                    "missing": False,
                    # Both start "now" - a brand new bag is assumed
                    # attended at the moment it's first seen (someone
                    # just set it down / it just entered frame);
                    # the unattended clock only starts ticking once
                    # association evidence actually stops.
                    "last_attended_time": now,
                    "last_weak_attended_time": now,
                }

            else:

                state = self.bags[bid]
                state["bbox"] = self._smooth(state["bbox"], b["bbox"])
                state["centroid"] = self._smooth(
                    state["centroid"], b["centroid"]
                )
                state["confidence"] = b["confidence"]
                state["last_seen"] = now
                state["missing"] = False

            self.bags[bid]["class_history"].append(b["class_name"])
            seen_ids.add(bid)

        # Grace-period carry-forward.
        for bid, state in self.bags.items():

            if bid in seen_ids:
                continue

            if "bbox" not in state:
                continue

            if now - state["last_seen"] <= config.TRACK_GRACE_SEC:
                state["missing"] = True
                seen_ids.add(bid)

        results = []

        for bid in seen_ids:

            state = self.bags[bid]

            # ---- Association: check EVERY active person, EVERY
            # frame, regardless of whether this bag was freshly
            # redetected this exact frame. This is the core fix. ----

            fully_attended = False
            weak_evidence = False

            for p in active_persons:

                overlap = _iou(state["bbox"], p["bbox"])
                distance = _centroid_distance(
                    state["centroid"], p["centroid"]
                )

                associated = (
                    overlap >= config.BAG_HOLD_IOU_THRESHOLD
                    or distance < config.PERSON_PROXIMITY_PX
                )

                if not associated:
                    continue

                if p["confirmed"]:
                    fully_attended = True
                else:
                    weak_evidence = True

            if fully_attended:
                state["last_attended_time"] = now
                state["last_weak_attended_time"] = now
            elif weak_evidence:
                state["last_weak_attended_time"] = now

            unattended_for = now - state["last_attended_time"]

            weak_recently = (
                now - state["last_weak_attended_time"]
                <= config.WEAK_ASSOCIATION_CAP_SEC
            )

            if unattended_for < config.UNCERTAIN_AFTER_SEC:
                level = "LOW"
            elif unattended_for < config.HIGH_ALERT_AFTER_SEC:
                level = "UNCERTAIN"
            elif weak_recently:
                # Enough time has passed to normally be HIGH, but
                # there's been recent (even if unconfirmed) person
                # activity around this bag - don't jump straight to
                # HIGH on that alone, but don't fully clear it either.
                level = "UNCERTAIN"
            else:
                level = "HIGH"

            stable_class = (
                Counter(state["class_history"]).most_common(1)[0][0]
                if state["class_history"]
                else "backpack"
            )

            results.append({
                "class_name": stable_class,
                "raw_class_name": (
                    state["class_history"][-1]
                    if state["class_history"]
                    else stable_class
                ),
                "confidence": state["confidence"],
                "bbox": state["bbox"],
                "centroid": state["centroid"],
                "object_id": bid,
                "threat_level": level,
                "unattended_seconds": round(unattended_for, 1),
                "attended": fully_attended,
                "predicted": state.get("missing", False),
            })

            if self.debug:

                tag = " (predicted/grace)" if state.get("missing") else ""

                print(f"[TRACKER] bag track_id={bid} class={stable_class}{tag}")

                if fully_attended:
                    note = "ATTENDED (confirmed person associated)"
                elif weak_evidence:
                    note = "weak evidence (unconfirmed person nearby)"
                else:
                    note = "no person evidence this frame"

                print(f"[ASSOCIATION] bag {bid}: {note}")

                print(
                    f"[THREAT] {stable_class} (id={bid}) "
                    f"unattended for {unattended_for:.1f}s -> {level}"
                )

        # Fully forget long-gone bags.
        for bid in list(self.bags):
            if (
                now - self.bags[bid]["last_seen"]
                > config.TRACK_FORGET_SEC
            ):
                del self.bags[bid]

        return results

    # ------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------

    def update(self, detections):
        """
        Takes this frame's filtered detections (from Detector.detect),
        updates both the person and bag registries, and returns the
        list of currently-visible BAG tracks (with threat_level,
        unattended_seconds, attended, predicted).

        Call get_visible_persons() afterward if you also want to draw
        the stabilized (grace-period-smoothed) person boxes.
        """

        now = time.time()

        raw_persons = [
            d for d in detections
            if d["class_name"] == config.PERSON_CLASS
        ]

        raw_bags = [
            d for d in detections
            if d["class_name"] in config.BAG_CLASSES
        ]

        active_persons = self._update_persons(raw_persons, now)

        self._active_persons_cache = active_persons

        return self._update_bags(raw_bags, now, active_persons)

    def get_visible_persons(self):
        """
        Stabilized (grace-period-surviving) person boxes for drawing.
        Call this AFTER update() for the same frame.
        """

        return [
            {
                "class_name": "person",
                "confidence": p["confidence"],
                "bbox": p["bbox"],
                "centroid": p["centroid"],
                "object_id": p["person_id"],
                "confirmed": p["confirmed"],
                "predicted": p["predicted"],
            }
            for p in self._active_persons_cache
        ]
