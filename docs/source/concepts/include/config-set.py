import earthkit.data

# Change the location of the user defined cache:
earthkit.data.config.set("user-cache-directory", "/big-disk/earthkit-data-cache")

# Change download timeout
earthkit.data.config.set("url-download-timeout", "1m")

# Multiple values can be set together. The argument list
# can be a dictionary:
earthkit.data.config.set({"url-download-timeout": "1m", "check-out-of-date-urls": True})

# Alternatively, we can use keyword arguments. However, because
# the “-” character is not allowed in variable names in Python we have
# to replace “-” with “_” in all the keyword arguments:
earthkit.data.config.set(url_download_timeout="1m", check_out_of_date_urls=True)
