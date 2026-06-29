from bucephalus.data.provider_adapters.base import KeyedAPIAdapter


class APIFootballAdapter(KeyedAPIAdapter):
    provider_name = "api_football"
    env_var = "API_FOOTBALL_KEY"
