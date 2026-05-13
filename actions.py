ACTION_REWARDS = {
    "voice": {
        "story_repost": 2,
        "feed_post": 6,
        "reddit_post": 6,
        "facebook_group_post": 6,
        "reel_short": 8,
        "detailed_review_thread": 10,
        "long_form_video": 14,
    },
    "atelier": {
        "painted_model_photo": 8,
        "printed_scene_photo": 8,
        "fan_art": 10,
        "diorama_full_scene": 12,
        "painting_process_reel": 10,
        "high_quality_photoset": 12,
        "major_showcase_project": 16,
    },
    "merchant": {
        "standard_core_backing": 10,
        "complete_full_set_backing": 16,
        "merchant_tier_backing": 30,
        "one_paid_addon_pack": 4,
        "late_pledge_completion": 8,
    },
    "wardens": {
        "printed_model_photo": 6,
        "print_report_with_settings": 8,
        "detailed_feedback_message": 6,
        "structured_review_issues_fixes": 10,
        "beta_test_summary": 12,
        "completed_feedback_mission": 8,
        "poll_participation": 1,
        "useful_issue_report_confirmed": 8,
    },
}


BONUS_REWARDS = {
    "voice": {
        "views_1000_or_100_reactions": 2,
        "views_5000_or_300_reactions": 4,
        "views_10000_or_1000_reactions": 6,
    },
    "atelier": {
        "strong_feature_worthy_work": 2,
        "studio_feature_tier_work": 4,
    },
    "merchant": {
        "three_plus_addons_bonus": 6,
        "second_campaign_in_row": 8,
        "third_campaign_in_row": 12,
        "fourth_plus_campaign_in_row": 15,
    },
    "wardens": {},
}


def get_action_marks(branch: str, action_key: str) -> int | None:
    return ACTION_REWARDS.get(branch, {}).get(action_key)


def get_bonus_marks(branch: str, bonus_key: str) -> int | None:
    return BONUS_REWARDS.get(branch, {}).get(bonus_key)


def get_action_choices_for_branch(branch: str) -> list[str]:
    return list(ACTION_REWARDS.get(branch, {}).keys())
