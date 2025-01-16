import earthkit.data

print(earthkit.data.config.get("number-of-download-threads"))

with earthkit.data.config.temporary():
    earthkit.data.config.set("number-of-download-threads", 12)
    print(earthkit.data.config.get("number-of-download-threads"))

# Temporary config can also be created with arguments:
with earthkit.data.config.temporary("number-of-download-threads", 11):
    print(earthkit.data.config.get("number-of-download-threads"))
