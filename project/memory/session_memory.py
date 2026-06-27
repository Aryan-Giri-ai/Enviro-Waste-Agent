"""
Memory Management
Short-term session memory (per active user session) and a
simple in-memory long-term user profile placeholder.

NOTE: Persistent storage (e.g. a real JSON/SQL database) is
intentionally NOT implemented here - that will be added later
per Database.md. UserProfileMemory currently lives only in
process memory and resets when the runtime restarts.
"""

import uuid
from datetime import datetime, timezone


class SessionMemory:
    """Holds the active, in-progress state for a single user session."""

    def __init__(self, session_id: str = None):
        self.session_id = session_id or str(uuid.uuid4())
        self.image_metadata = None
        self.location_query = None
        self.task_list = []
        self.worker_responses = {}
        self.evaluator_reviews = []
        self.final_report = None
        self.created_at = datetime.now(timezone.utc).isoformat()

    def set_input(self, image_metadata=None, location_query=None):
        self.image_metadata = image_metadata
        self.location_query = location_query

    def set_task_list(self, tasks: list):
        self.task_list = tasks

    def store_worker_response(self, worker_name: str, response):
        self.worker_responses[worker_name] = response

    def add_evaluator_review(self, review: dict):
        self.evaluator_reviews.append(review)

    def set_final_report(self, report: str):
        self.final_report = report

    def reset(self):
        self.__init__(session_id=self.session_id)

    def to_dict(self):
        return {
            "session_id": self.session_id,
            "image_metadata": self.image_metadata,
            "location_query": self.location_query,
            "task_list": self.task_list,
            "worker_responses": self.worker_responses,
            "evaluator_reviews": self.evaluator_reviews,
            "final_report": self.final_report,
            "created_at": self.created_at,
        }


class UserProfileMemory:
    """
    Lightweight in-memory stand-in for persistent long-term user
    profile storage. Will be backed by a real database later
    (see Database.md - not implemented yet).
    """

    _profiles = {}

    def __init__(self, user_id: str = "default_user"):
        self.user_id = user_id
        if user_id not in UserProfileMemory._profiles:
            UserProfileMemory._profiles[user_id] = {
                "preferred_location": None,
                "lifetime_sorted_count": 0,
                "saved_carbon_estimate": 0.0,
                "achievement_badges": [],
            }

    @property
    def profile(self):
        return UserProfileMemory._profiles[self.user_id]

    def set_preferred_location(self, location: str):
        self.profile["preferred_location"] = location

    def record_sorted_item(self, carbon_offset_kg: float = 0.0):
        self.profile["lifetime_sorted_count"] += 1
        self.profile["saved_carbon_estimate"] += carbon_offset_kg
        self._maybe_award_badge()

    def _maybe_award_badge(self):
        count = self.profile["lifetime_sorted_count"]
        badges = self.profile["achievement_badges"]
        milestones = {5: "Getting Started", 25: "Eco Apprentice", 100: "Eco Champion"}
        for threshold, badge in milestones.items():
            if count >= threshold and badge not in badges:
                badges.append(badge)

    def get_profile(self):
        return dict(self.profile)
