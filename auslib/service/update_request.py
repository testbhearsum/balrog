import logging
from random import randint

from auslib.global_state import cache, dbo
from auslib.util.rulematching import matchBoolean, matchBuildID, matchChannel, matchCsv, matchLocale, matchMemory, matchSimpleExpression, matchVersion


# TODO: what's the right way to do this in python3?
# Magic constants that callers can use to choose a specific "random" result.
SUCCEED = 1
FAIL = -1

# TODO: move this
def getFallbackChannel(channel):
    return channel.split("-cck-")[0]

def emergency_shutoff_status(product, channels, transaction):
    for channel in channels:
        cache_key = (product, channel)
        v = cache.get("updates_disabled", cache_key)
        if v is not None:
            return v

        v = bool(dbo.emergencyShutoffs.select(where={"product": product, "channel": channel}, transaction=transaction))
        cache.put("updates_disabled", cache_key, v)
        return v


def matching_rule(query, transaction):
    rules = []
    # TODO: can we sort descending in the query, to avoid sorting?
    for rule in sorted(dbo.rules.select(transaction=transaction), key=lambda rule: rule["priority"], reverse=True):
        # TODO: may not work with distVersion because it doesn't exist in query version 1
        basic_match = True
        # TODO: this part isn't working
        for field in ("product", "buildTarget", "headerArchitecture", "distVersion"):
            if rule[field] and rule[field] != query.get(field):
                print(f"{field} didn't match for {rule['mapping']}")
                print(rule[field])
                print(query.get(field))
                basic_match = False
                break
        # Break if any of the fields above didn't match
        if not basic_match:
            print("broke")
            continue

        print(rule["mapping"])
        # Resolve special means for channel, version, and buildID - dropping
        # rules that don't match after resolution.
        if not matchChannel(rule["channel"], query["channel"], getFallbackChannel(query["channel"])):
            logging.debug("%s doesn't match %s", rule["channel"], query["channel"])
            continue
        if not matchVersion(rule["version"], query["version"]):
            logging.debug("%s doesn't match %s", rule["version"], query["version"])
            continue
        if not matchBuildID(rule["buildID"], query["buildID"]):
            logging.debug("%s doesn't match %s", rule["buildID"], query["buildID"])
            continue
        if not matchMemory(rule["memory"], query.get("memory", None)):
            logging.debug("%s doesn't match %s", rule["memory"], query.get("memory"))
            continue
        # To help keep the rules table compact, multiple OS versions may be
        # specified in a single rule. They are comma delimited, so we need to
        # break them out and create clauses for each one.
        if not matchSimpleExpression(rule["osVersion"], query["osVersion"]):
            logging.debug("%s doesn't match %s", rule["osVersion"], query["osVersion"])
            continue
        if not matchCsv(rule["instructionSet"], query.get("instructionSet", ""), substring=False):
            logging.debug("%s doesn't match %s", rule["instructionSet"], query.get("instructionSet"))
            continue
        if not matchCsv(rule["distribution"], query.get("distribution", ""), substring=False):
            logging.debug("%s doesn't match %s", rule["distribution"], query.get("distribution"))
            continue
        # Locales may be a comma delimited rule too, exact matches only
        if not matchLocale(rule["locale"], query["locale"]):
            logging.debug("%s doesn't match %s", rule["locale"], query["locale"])
            continue
        if not matchBoolean(rule["mig64"], query.get("mig64")):
            logging.debug("%s doesn't match %s", rule["mig64"], query.get("mig64"))
            continue
        if not matchBoolean(rule["jaws"], query.get("jaws")):
            logging.debug("%s doesn't match %s", rule["jaws"], query.get("jaws"))
            continue

        rules.append(rule)

    print("THE END")
    print(rules)
    return rules[0]


def matching_releases(query, transaction):
    # Underlying code depends on osVersion being set. Since this route only
    # exists to support ancient queries, and all newer versions have osVersion
    # in them it's easier to set this here than make the all of the underlying
    # code support queries without it.
    if query["queryVersion"] == 1:
        query["osVersion"] = ""

    fallback_channel = getFallbackChannel(query["channel"])
    if emergency_shutoff_status(query["product"], (query["channel"], fallback_channel), transaction) is True:
        return None, None

    # TODO: should/can this move to client.py, and have the result passed in?
    rule = matching_rule(query, transaction)
    if not rule or not rule["mapping"]:
        return None, None

    blob = dbo.releases.getReleaseBlob(name=rule["mapping"], transaction=transaction)
    if not query["force"] == SUCCEED and rule["backgroundRate"] < 100:
        if query["force"] == FAIL or randint(0, 99) > rule["backgroundRate"]:
            if rule["fallbackMapping"]:
                blob = dbo.releases.getReleaseBlob(name=rule["fallbackMapping"], transaction=transaction)

            return None, None

    if not blob.shouldServeUpdate(query):
        return None, None

    response_blobs = []
    for product in blob.getResponseProducts():
        product_query = query.copy()
        product_query["product"] = product
        response_blob = matching_rule(product_query, transaction)
        response_blobs.append({"blob": response_blob, "query": product_query})
    for blob_name in blob.getResponseBlobs():
        product_query = query.copy()
        product = dbo.releases.getReleases(name=blob_name, limit=1, transaction=transaction)[0]["product"]
        product_query["product"] = product
        response_blob = dbo.releases.getReleaseBlob(name=blob_name, transaction=transaction)
        response_blobs.append({"blob": response_blob, "query": product_query})

    return {"blob": blob, "query": query}, response_blobs


def update_xml(blob, response_blobs, whitelisted_domains, special_force_hosts):
    if not blob:
        xml = ['<?xml version="1.0"?>']
        xml.append("<updates>")
        xml.append("</updates>")
        xml = "\n".join(xml)
        return xml

    if not response_blobs:
        response_blobs.append(blob)
        
    xml = blob.getHeaderXML()
    xml.append(release.getInnerHeaderXML(query, "minor", whitelisted_domains, special_force_hosts))
    for response_blob in response_blobs:
        xml.extend(
            response_blob["blob"].getInnerXML(
                response_blob["query"], "minor", whitelisted_domains, special_force_hosts)
        )
    # Appending Footer
    # In case of superblob Extracting Header form parent release
    xml.append(release.getInnerFooterXML(query, "minor", whitelisted_domains, special_force_hosts))
    xml.append(release.getFooterXML())
    # ensure valid xml by using the right entity for ampersand
    return re.sub("&(?!amp;)", "&amp;", "\n".join(xml))
