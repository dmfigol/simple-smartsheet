from marshmallow import EXCLUDE, RAISE


def get_unknown_field_handling(debug: bool) -> str:
    if debug:
        return RAISE
    else:
        return EXCLUDE
