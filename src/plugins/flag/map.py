import math

from plugins.flag.base import FlagPlugin


class MapFlagPlugin(FlagPlugin):
    name = "map"

    def check(self, flag, *args, **kwargs):
        r = 6373.0

        correct_latlon = self.challenge.flag_metadata["location"]
        lat1, lon1 = math.radians(flag[0]), math.radians(flag[1])
        lat2, lon2 = math.radians(correct_latlon[0]), math.radians(correct_latlon[1])

        lon_diff = lon2 - lon1
        lat_diff = lat2 - lat1

        a = math.sin(lat_diff / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(lon_diff / 2) ** 2
        distance = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a)) * r

        return self.challenge.flag_metadata["radius"] > distance

    def self_check(self):
        """Ensure the set flag metadata has the required properties"""
        issues = []

        if not self.challenge.flag_metadata.get("radius", ""):
            issues.append("property 'radius' must be set!")
        elif not self.challenge.flag_metadata.get("radius", "").replace(".", "").isnumeric():
            issues.append("property 'radius' must be numeric!")

        if not self.challenge.flag_metadata.get("location", []):
            issues.append("property 'location' must be set!")
        elif type(self.challenge.flag_metadata.get("location", None)) is not list:
            issues.append("property 'location' must be an array of len 2!")
        elif len(self.challenge.flag_metadata.get("location", [])) != 2:
            issues.append("property 'location' must be an array of len 2!")

        return issues
