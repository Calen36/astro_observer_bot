from dadata import DadataAsync
from config import DADATA_TOKEN, DADATA_SECRET


async def get_geodata(string):
    async with DadataAsync(DADATA_TOKEN, DADATA_SECRET) as dadata:
        result = await dadata.clean("address", string)
        return result['result'], result['geo_lat'], result['geo_lon']
