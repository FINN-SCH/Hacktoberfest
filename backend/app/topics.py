"""Predefined grammar topics per target language (PLAN.md section 3). Frozen after hour 1."""

TOPICS: dict[str, dict[str, str]] = {
    "de": {
        "de_perfekt_auxiliary": "Perfekt: haben vs. sein",
        "de_past_participle": "Partizip II forms",
        "de_verb_conjugation": "Present-tense conjugation",
        "de_verb_second": "Verb in second position",
        "de_verb_final_subclause": "Verb at the end of subordinate clauses",
        "de_separable_verbs": "Separable verbs",
        "de_modal_infinitive": "Modal verb + infinitive",
        "de_noun_gender": "Noun gender (der/die/das)",
        "de_accusative": "Accusative case",
        "de_dative": "Dative case",
        "de_two_way_prepositions": "Two-way prepositions",
        "de_preposition_choice": "Preposition choice",
        "de_adjective_endings": "Adjective endings",
        "de_plural": "Plural forms",
        "de_pronouns": "Pronouns",
        "de_negation": "nicht vs. kein",
        "de_vocabulary_choice": "Word choice",
        "de_other": "Other",
    },
    "en": {
        "en_third_person_s": "3rd person -s",
        "en_past_simple_irregular": "Irregular past forms",
        "en_present_perfect_vs_past": "Present perfect vs. past simple",
        "en_continuous_vs_simple": "Continuous vs. simple",
        "en_future_forms": "will / going to",
        "en_question_formation": "Questions and do-support",
        "en_subject_verb_agreement": "Subject-verb agreement",
        "en_articles": "a / an / the / no article",
        "en_countable_uncountable": "Countable vs. uncountable",
        "en_prepositions": "Prepositions",
        "en_comparatives": "Comparatives and superlatives",
        "en_pronouns": "Pronouns",
        "en_vocabulary_choice": "Word choice",
        "en_other": "Other",
    },
}


def is_valid_topic(topic: str, language: str) -> bool:
    return topic in TOPICS.get(language, {})


def topic_label(topic: str) -> str:
    for lang_topics in TOPICS.values():
        if topic in lang_topics:
            return lang_topics[topic]
    return topic
