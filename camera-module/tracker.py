import time
import math
import config


class ObjectTracker:
    """
    Tracks bags across frames and determines
    LOW / UNCERTAIN / HIGH threat levels.
    """

    def __init__(self):
        self.tracked = {}
        self.next_id = 0

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

        results = []

        for bag in bags:

            obj_id = self._match_or_create(
                bag["centroid"],
                now
            )

            state = self.tracked[obj_id]

            state["centroid"] = bag["centroid"]
            state["last_seen"] = now

            person_nearby = any(
                math.hypot(
                    bag["centroid"][0] - person[0],
                    bag["centroid"][1] - person[1]
                ) < config.PERSON_PROXIMITY_PX
                for person in persons
            )

            if person_nearby:
                state["last_person_nearby"] = now

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
                **bag,
                "object_id": obj_id,
                "threat_level": level,
                "unattended_seconds": round(
                    unattended_for,
                    1
                ),
            })

        # Remove objects that disappeared
        # for more than 5 seconds.

        for obj_id in list(self.tracked):

            if (
                now
                - self.tracked[obj_id]["last_seen"]
                > 5
            ):
                del self.tracked[obj_id]

        return results