"""Grammar topics taxonomy for English and German (from PLAN.md)"""

TOPICS = {
    "en": {
        "en_subject_verb_agreement": "Subject-Verb Agreement",
        "en_past_simple_irregular": "Irregular Past Forms",
        "en_present_perfect_vs_past": "Present Perfect vs. Past Simple",
        "en_third_person_s": "3rd Person -s",
        "en_continuous_vs_simple": "Continuous vs. Simple Tense",
        "en_future_forms": "Future Forms (will / going to)",
        "en_question_formation": "Question Formation & Auxiliaries",
        "en_articles": "Articles (a / an / the)",
        "en_prepositions": "Preposition Choice",
        "en_comparatives": "Comparatives & Superlatives",
        "en_countable_uncountable": "Countable vs. Uncountable",
        "en_pronouns": "Pronouns",
        "en_vocabulary_choice": "Word Choice & Phrasing",
        "en_other": "General Grammar"
    },
    "de": {
        "de_perfekt_auxiliary": "Perfekt: haben vs. sein",
        "de_past_participle": "Partizip II Formen",
        "de_verb_conjugation": "Präsens-Konjugation",
        "de_verb_second": "Verb an 2. Position (Hauptsatz)",
        "de_verb_final_subclause": "Verb am Ende (Nebensatz)",
        "de_separable_verbs": "Trennbare Verben",
        "de_modal_infinitive": "Modalverb + Infinitiv",
        "de_noun_gender": "Genus (der / die / das)",
        "de_accusative": "Akkusativ",
        "de_dative": "Dativ",
        "de_two_way_prepositions": "Wechselpräpositionen",
        "de_preposition_choice": "Präpositionswahl",
        "de_adjective_endings": "Adjektivendungen",
        "de_plural": "Pluralformen",
        "de_negation": "nicht vs. kein",
        "de_vocabulary_choice": "Wortwahl & Ausdruck",
        "de_other": "Allgemeine Grammatik"
    }
}

def get_topic_label(topic_id: str, lang: str = "en") -> str:
    lang_topics = TOPICS.get(lang, {})
    return lang_topics.get(topic_id, TOPICS.get("en", {}).get(topic_id, topic_id.replace("en_", "").replace("de_", "").replace("_", " ").title()))
