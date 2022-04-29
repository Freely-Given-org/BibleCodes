# BibleCodes

A registry of short Bible version codes, e.g., KJV for King James Version. However, like most Bibles, there's different editions so KJV-1611 is quite different from KJV-1769.

## History

Most Bible study software displays multiple different Bible versions and so typically they create their own short reference codes.
However, this is an attempt to provide a registry of codes that publishers can add to (and correct)
and which will be used as a part of the [Bible Reference system](https://github.com/Freely-Given-org/BibleReferences)
and hence the syntax is restrained by compatibility with that.

This data was originally hosted [here](https://Freely-Given.org/BibleReference/BibleVersions/) and part of [this](https://github.com/Freely-Given-org/BibleOrgSys/blob/main/BibleOrgSys/DataFiles/BibleOrganisationalSystems.xml).

## Aims

- To provide a short (2-8 character) abbreviation for a Bible version
- Must not contain whitespace (so it's a single token)
- To avoid clashes when a publisher is looking for new abbreviation (remembering that Bibles are published in many languages)
- To be able to have a 4-digit publication year appended as necessary, e.g., KJV-1611
- To be able to have an edition string appended as necessary KJV!MBS_1997_Printing or KJV-1769!MBS_1997_Printing
