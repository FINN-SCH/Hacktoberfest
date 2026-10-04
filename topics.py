"""Grammar topics taxonomy for multi-language tutor (English, German, Spanish, French, Italian)"""

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
    },
    "es": {
        "es_ser_vs_estar": "Ser vs. Estar",
        "es_por_vs_para": "Por vs. Para",
        "es_subjunctive": "Subjuntivo",
        "es_preterite_imperfect": "Pretérito Indefinido vs. Imperfecto",
        "es_gender_agreement": "Concordancia de Género y Número",
        "es_direct_indirect_pronouns": "Pronombres Objeto Directo e Indirecto",
        "es_reflexive_verbs": "Verbos Reflexivos",
        "es_prepositions": "Uso de Preposiciones",
        "es_vocabulary_choice": "Vocabulario y Expresión",
        "es_other": "Gramática General"
    },
    "fr": {
        "fr_passe_compose_imparfait": "Passé Composé vs. Imparfait",
        "fr_etre_avoir": "Être vs. Avoir (Auxiliaires)",
        "fr_gender_agreement": "Accord en Genre et Nombre",
        "fr_articles": "Articles (Partitifs, Définis)",
        "fr_pronouns": "Pronoms (COI, COD, y, en)",
        "fr_subjunctive": "Subjonctif",
        "fr_prepositions": "Choix des Prépositions",
        "fr_negation": "Négation (ne... pas)",
        "fr_vocabulary_choice": "Vocabulaire et Tournure",
        "fr_other": "Grammaire Générale"
    },
    "it": {
        "it_essere_avere": "Essere vs. Avere",
        "it_passato_prossimo_imperfetto": "Passato Prossimo vs. Imperfetto",
        "it_gender_agreement": "Accordo di Genere e Numero",
        "it_articles_prepositions": "Preposizioni Articolate",
        "it_pronouns": "Pronomi Diretti e Indiretti (ci, ne)",
        "it_subjunctive": "Congiuntivo",
        "it_vocabulary_choice": "Vocabolario e Scelta Lessicale",
        "it_other": "Grammatica Generale"
    }
}

def get_topic_label(topic_id: str, lang: str = "en") -> str:
    # 1. Check specified language dictionary
    if lang in TOPICS and topic_id in TOPICS[lang]:
        return TOPICS[lang][topic_id]

    # 2. Check if topic key prefix maps to a known language
    prefix = topic_id.split("_")[0] if "_" in topic_id else ""
    if prefix in TOPICS and topic_id in TOPICS[prefix]:
        return TOPICS[prefix][topic_id]

    # 3. Search across all languages
    for l_dict in TOPICS.values():
        if topic_id in l_dict:
            return l_dict[topic_id]

    # 4. Clean fallback formatting
    clean = topic_id
    for p in ["en_", "de_", "es_", "fr_", "it_"]:
        if clean.startswith(p):
            clean = clean[len(p):]
            break
    return clean.replace("_", " ").title()
