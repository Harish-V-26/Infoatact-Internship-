from .token_vault import TokenVault

_vault = TokenVault()

def create_or_get_token(entity_type, value):
    return _vault.tokenize(entity_type, value)
