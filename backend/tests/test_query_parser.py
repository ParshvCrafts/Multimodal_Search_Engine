import pytest
from backend.app.engine.query_parser import QueryParser, ParsedQuery


@pytest.fixture
def parser():
    return QueryParser()


class TestCategoryParsing:
    def test_dress(self, parser):
        result = parser.parse("black midi dress")
        assert result.category_filter == "Dresses"

    def test_jacket(self, parser):
        result = parser.parse("leather jacket")
        assert result.category_filter == "Coats & Jackets"

    def test_jeans(self, parser):
        result = parser.parse("blue jeans")
        assert result.category_filter == "Jeans"

    def test_hoodie(self, parser):
        result = parser.parse("oversized hoodie")
        assert result.category_filter == "Hoodies & Sweatshirts"

    def test_trainers(self, parser):
        result = parser.parse("white trainers")
        assert result.category_filter == "Shoes"

    def test_bag(self, parser):
        result = parser.parse("leather bag")
        assert result.category_filter == "Bags"

    def test_no_category(self, parser):
        result = parser.parse("something nice")
        assert result.category_filter is None

    def test_multi_word_category(self, parser):
        result = parser.parse("puffer jacket warm")
        assert result.category_filter == "Coats & Jackets"


class TestColorParsing:
    def test_basic_color(self, parser):
        result = parser.parse("black dress")
        assert result.color_filter == "black"

    def test_synonym_color(self, parser):
        result = parser.parse("scarlet top")
        assert result.color_filter == "red"

    def test_navy(self, parser):
        result = parser.parse("navy blazer")
        assert result.color_filter == "navy"

    def test_multi_word_color(self, parser):
        result = parser.parse("sky blue dress")
        assert result.color_filter == "blue"

    def test_no_color(self, parser):
        result = parser.parse("casual hoodie")
        assert result.color_filter is None


class TestPriceParsing:
    def test_under(self, parser):
        result = parser.parse("dress under £40")
        assert result.price_max == 40.0
        assert result.price_min is None

    def test_over(self, parser):
        result = parser.parse("jacket over £100")
        assert result.price_min == 100.0

    def test_range(self, parser):
        result = parser.parse("shoes £20-£50")
        assert result.price_min == 20.0
        assert result.price_max == 50.0

    def test_budget(self, parser):
        result = parser.parse("budget dress")
        assert result.price_max == 30.0

    def test_luxury(self, parser):
        result = parser.parse("luxury jacket")
        assert result.price_min == 100.0

    def test_no_price(self, parser):
        result = parser.parse("blue dress")
        assert result.price_min is None
        assert result.price_max is None


class TestGenderParsing:
    def test_mens(self, parser):
        result = parser.parse("mens hoodie")
        assert result.gender_filter == "Men"

    def test_womens(self, parser):
        result = parser.parse("for women dress")
        assert result.gender_filter == "Women"

    def test_ladies(self, parser):
        result = parser.parse("ladies dress elegant")
        assert result.gender_filter == "Women"

    def test_no_gender(self, parser):
        result = parser.parse("casual hoodie")
        assert result.gender_filter is None


class TestMaterialParsing:
    def test_silk(self, parser):
        result = parser.parse("silk midi dress")
        assert result.material_filter == "silk"

    def test_leather(self, parser):
        result = parser.parse("leather jacket")
        assert result.material_filter == "leather"

    def test_denim(self, parser):
        result = parser.parse("denim jacket")
        assert result.material_filter == "denim"

    def test_no_material(self, parser):
        result = parser.parse("black dress")
        assert result.material_filter is None


class TestSizeParsing:
    def test_named_size(self, parser):
        result = parser.parse("size small hoodie")
        assert result.size_filter == "S"

    def test_numeric_size(self, parser):
        result = parser.parse("size 10 dress")
        assert result.size_filter == "10"

    def test_xl(self, parser):
        result = parser.parse("XL casual shirt")
        assert result.size_filter == "XL"

    def test_no_size(self, parser):
        result = parser.parse("black dress")
        assert result.size_filter is None


class TestExclusions:
    def test_not(self, parser):
        result = parser.parse("black dress not floral")
        assert "floral" in result.exclusions

    def test_without(self, parser):
        result = parser.parse("jacket without leather")
        assert "leather" in result.exclusions

    def test_no_keyword(self, parser):
        result = parser.parse("summer top no black")
        assert "black" in result.exclusions

    def test_material_exclusion_conflict(self, parser):
        result = parser.parse("jacket not cotton")
        assert result.material_filter is None
        assert "cotton" in result.exclusions

    def test_no_exclusions(self, parser):
        result = parser.parse("black dress")
        assert result.exclusions == []


class TestStyleTags:
    def test_single_tag(self, parser):
        result = parser.parse("casual hoodie")
        assert "casual" in result.style_tags

    def test_multiple_tags(self, parser):
        result = parser.parse("vintage boho dress")
        assert "vintage" in result.style_tags
        assert "boho" in result.style_tags

    def test_no_tags(self, parser):
        result = parser.parse("blue jeans")
        assert "casual" not in result.style_tags


class TestVibeText:
    def test_preserves_raw_query(self, parser):
        result = parser.parse("black dress under £40")
        assert result.raw_query == "black dress under £40"

    def test_vibe_not_empty(self, parser):
        result = parser.parse("black dress")
        assert len(result.vibe_text) > 0
