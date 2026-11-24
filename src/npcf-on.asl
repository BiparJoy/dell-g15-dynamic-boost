// Sets Dell's Dynamic Boost flag (NVDB) for this boot only. Refuses unless the firmware mailbox markers and GPU generation match.
DefinitionBlock ("npcf-on.aml", "SSDT", 2, "LOCAL", "NPCFON", 0x00000001)
{
    External (\DSNH, FieldUnitObj)
    External (\DSNT, FieldUnitObj)
    External (\NVDB, FieldUnitObj)
    External (\_SB.PC00.PEG1.PEGP.NGEN, IntObj)

    If (LAnd (LAnd (LEqual (\DSNH, 0x44414548), LEqual (\DSNT, 0x4C494154)), LEqual (\_SB.PC00.PEG1.PEGP.NGEN, 0x14)))
    {
        Store (One, \NVDB)
    }
}
