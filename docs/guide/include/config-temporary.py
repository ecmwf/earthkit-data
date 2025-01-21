import earthkit.data

print(earthkit.data.config.get("url-download-timeout"))

with earthkit.data.config.temporary():
    earthkit.data.config.set("url-download-timeout", 5)
    print(earthkit.data.config.get("url-download-timeout"))

# Temporary config can also be created with arguments:
with earthkit.data.config.temporary("url-download-timeout", 11):
    print(earthkit.data.config.get("url-download-timeout"))
