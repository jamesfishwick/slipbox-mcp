"""Tests for LinkType.inverse property."""
from slipbox_mcp.models.schema import LinkType


class TestLinkTypeInverse:
    def test_extends_inverse_is_extended_by(self):
        assert LinkType.EXTENDS.inverse == LinkType.EXTENDED_BY

    def test_extended_by_inverse_is_extends(self):
        assert LinkType.EXTENDED_BY.inverse == LinkType.EXTENDS

    def test_reference_inverse_is_reference(self):
        assert LinkType.REFERENCE.inverse == LinkType.REFERENCE

    def test_related_inverse_is_related(self):
        assert LinkType.RELATED.inverse == LinkType.RELATED

    def test_all_types_have_inverse(self):
        for lt in LinkType:
            assert hasattr(lt, "inverse"), f"{lt} missing inverse property"

    def test_inverse_is_symmetric(self):
        for lt in LinkType:
            assert lt.inverse.inverse == lt, f"{lt}.inverse.inverse != {lt}"
