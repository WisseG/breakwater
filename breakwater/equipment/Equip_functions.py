def install_set_true(df, equip):

    df2 = df[df[equip].notna()]

    return  len(df) == len(df2)


