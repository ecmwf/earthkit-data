import earthkit.data

# Change the location of the cache:
earthkit.data.settings.set("cache-directory", "/big-disk/earthkit-data-cache")

# Set some default plotting options (e.g. all maps will
# be 400 pixels wide by default):
earthkit.data.settings.set("plotting-options", width=400)
