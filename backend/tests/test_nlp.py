from backend.app.engine.nlp import MultilingualHandler, SpellCorrector


class TestMultilingualHandler:
    def test_english_detected(self):
        lang = MultilingualHandler.detect_language("black leather jacket")
        assert lang == "en"

    def test_french_detected(self):
        lang = MultilingualHandler.detect_language("robe noir pour la femme")
        assert lang == "fr"

    def test_german_detected(self):
        lang = MultilingualHandler.detect_language("das kleid ist für die frau")
        assert lang == "de"

    def test_spanish_detected(self):
        lang = MultilingualHandler.detect_language("el vestido rojo para la mujer")
        assert lang == "es"

    def test_translate_french(self):
        translated, lang, was_translated = MultilingualHandler.translate_query("robe noir")
        assert "dress" in translated
        assert "black" in translated
        assert was_translated is True

    def test_english_passthrough(self):
        translated, lang, was_translated = MultilingualHandler.translate_query("black dress")
        assert translated == "black dress"
        assert was_translated is False
        assert lang == "en"

    def test_spanish_translate(self):
        translated, lang, was_translated = MultilingualHandler.translate_query("vestido rojo")
        assert "dress" in translated
        assert "red" in translated

    def test_cjk_detected(self):
        lang = MultilingualHandler.detect_language("黒いドレス")
        assert lang in ("ja", "zh")

    def test_non_latin_passthrough(self):
        translated, lang, was_translated = MultilingualHandler.translate_query("黒いドレス")
        assert was_translated is False


class TestSpellCorrector:
    def test_correct_known_word(self):
        sc = SpellCorrector()
        sc.fit(["black leather jacket dress shoes boots"])
        corrected = sc.correct_word("blak")
        assert corrected == "black"

    def test_no_correction_needed(self):
        sc = SpellCorrector()
        sc.fit(["black leather jacket"])
        corrected = sc.correct_word("black")
        assert corrected == "black"

    def test_query_correction(self):
        sc = SpellCorrector()
        sc.fit(["black leather jacket dress shoes boots trainers hoodie"])
        result, was_corrected = sc.correct_query("blak lether jaket")
        assert was_corrected is True
        assert "black" in result

    def test_short_words_skipped(self):
        sc = SpellCorrector()
        sc.fit(["black leather jacket"])
        corrected = sc.correct_word("an")
        assert corrected == "an"

    def test_price_tokens_skipped(self):
        sc = SpellCorrector()
        sc.fit(["black dress"])
        result, _ = sc.correct_query("dress £40")
        assert "£40" in result

    def test_not_ready_passthrough(self):
        sc = SpellCorrector()
        result, was_corrected = sc.correct_query("blak dress")
        assert result == "blak dress"
        assert was_corrected is False
