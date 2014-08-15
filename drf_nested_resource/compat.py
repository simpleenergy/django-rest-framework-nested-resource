def dumb_singular_noun(word, count=None):
    """
    *dumb* implementation of the `inflect` library's `singular_noun` function which simply strips off a trailing 's' if present.
    """
    if word[-1] == 's':
        return word[:-1]
    return word

try:
    import inflect
    engine = inflect.engine()
    singular_noun = engine.singular_noun
except ImportError:
    singular_noun = dumb_singular_noun
