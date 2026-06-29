from bucephalus.data.provider_adapters.base import KeyedAPIAdapter


class FootballDataAdapter(KeyedAPIAdapter):
    provider_name = "football_data"
    env_var = "FOOTBALL_DATA_KEY"
