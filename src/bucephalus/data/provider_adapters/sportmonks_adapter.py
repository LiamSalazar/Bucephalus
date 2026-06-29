from bucephalus.data.provider_adapters.base import KeyedAPIAdapter


class SportmonksAdapter(KeyedAPIAdapter):
    provider_name = "sportmonks"
    env_var = "SPORTMONKS_KEY"
