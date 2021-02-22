# def get_data(x):
#     sql_get_data = f"""
#
# select inv.itemno, it.SKEY,  NAME, inv.suplno,  stockid, CONVERT(varchar,convert(decimal(10,2),INVFIG), 100), SHELF, Isnull(it.note,'') as note  from INVTS01 inv
# join item it
# on it.itemno = inv.itemno and it.SUPLNO = inv.SUPLNO
#
# where inv.invtno = '{x}'
# order by inv.SHELF
# """
#     return sql_get_data


def get_data(x):
    return f"""
select * from (
select inv.itemno, max(it.SKEY) SKEY,  max(NAME) NAME, stockid, sum(convert(float,inv.INVFIG)) INVFIG, max(SHELF) shelf , max(convert(varchar(max),isnull(it.note,''))) as note  from INVTS01 inv
join item it
on it.itemno = inv.itemno and it.SUPLNO = inv.SUPLNO

where inv.invtno = {x}
group by  inv.itemno,stockid ) a 
order by a.shelf,a.itemno"""

def get_name_from_block_latter(invtno):
    return f"""select name  from amintegrations.dbo.invblock
where inv_vno = '{invtno}'"""

def chack_part_in_invtno(invtno,itemno, suplno):
    return f"""if exists
(select * from INVTS01
where invtno='{invtno}')
begin
select itemno, suplno from INVTS01
where itemno='{itemno}' and SUPLNO='{suplno}'and invtno='{invtno}'
end
else select '0'"""


def check_later_for_exist(latter):
    return f"""if exists (select top 1  * from INVTS01 where invtno={latter})
begin select '1'
end
else select '0'"""

def check_in_base(x):
    return f"""if exists
(select * from amintegrations.dbo.invblock
where inv_vno='{x}')
begin
select name from amintegrations.dbo.invblock
where inv_vno='{x}'
end
else select '0'"""

#                                                               CONVERT(varchar,convert(decimal(10,2),INVFIG), 100)
def get_parts_from_OSFI(x):
    return f"""
SELECT item.ITEMNO, max(item.SKEY) skey, max(item.name) name,osfi.STOCKID, max(OSFI.SHELF1) shelf1, max(convert(varchar(max),ITEM.NOTE)) note
FROM osfi
JOIN item
ON item.itemno = osfi.itemno and
item.SUPLNO = osfi.SUPLNO
where osfi.itemno = '{x}'  and OSFI.STOCKFIG>0
group by item.itemno,osfi.STOCKID

"""

def add_to_first_window(x, y):
    return f"""SELECT item.ITEMNO, item.SKEY, item.name, item.SUPLNO, OSFI.STOCKID,  CONVERT(varchar,convert(decimal(10,2), OSFI.STOCKFIG), 100), isnull(OSFI.SHELF1,'') as SHELF1, isnull(ITEM.NOTE, '') as note
FROM item
LEFT JOIN osfi
ON item.itemno = osfi.itemno and
 item.SUPLNO = osfi.SUPLNO
where item.itemno = '{x}' and  item.suplno='{y}'"""

def listblock(sheet, x):
    return f"""insert into amintegrations.dbo.invblock
values ('{sheet}', '{x}')"""


def del_from_listblock(sheet, name):
    return f"""
delete from amintegrations.dbo.invblock
where inv_vno = '{sheet}' and name = '{name}'
select @@ROWCOUNT"""


def update_invt(invtno, INVFIG, ITEMNO, SUPLNO, STOCKID):
    return f"""update INVTS01 set INVFIG={INVFIG} where invtno='{invtno}' and ITEMNO='{ITEMNO}' and SUPLNO='{SUPLNO}' and STOCKID='{STOCKID}'
"""


def check_in_another_sheets(ITEMNO, intvno):
    return f"""select itemno,INVTNO, shelf from INVTS01
where ITEMNO='{ITEMNO}' and   UPDATED=0  and invtno<>{intvno}
"""

def unclose(invtno):
    return f"""delete  
  FROM [amintegrations].[dbo].[iminvtblock]

  where invtno = {invtno}
"""

def may_i_coming(invtno):
    return f"""select * from [amintegrations].[dbo].[iminvtblock]
where invtno = '{invtno}'"""
# ##################################### не забыть исправить UPDATED=1 на ноль 0


def close_edit(invtno, status):
    return f"""INSERT INTO  [amintegrations].[dbo].[iminvtblock]
values({invtno}, '{status}')"""


def secret(inv_vno, user):
    return f"""
    delete from amintegrations.dbo.invblock
where inv_vno = '{inv_vno}' and name = '{user}'
select @@ROWCOUNT"""



def add_new_row_for_latter(INVTNO,itemno, suplno):
    return f"""
    DECLARE @cnt int
declare @recid int
set @recid=(select max(recordid) from INVTS01 where INVTNO={INVTNO})
SET @cnt = (select max(ono) from INVTS01 where INVTNO={INVTNO})

insert into INVTS01 (INVTNO,ono,ITEMNO,SUPLNO,INVFIG,SHELF,STOCKFIG,STOCKID,UPDATED,RECORDID)
select  {INVTNO} as invtno,(row_number() OVER (ORDER BY itemno ASC))+@cnt As ono,itemno,suplno,0 as invfig,shelf1 as shelf,stockfig,STOCKID,0 as updated,@recid as recordid from osfi where itemno='{itemno}'
and suplno='{suplno}'
    """

def check_sum(invtno, itemno):
    return f"""select i.itemno, i.suplno, convert(float,s.AVGPR) AVGPR ,convert(float,sum(i.STOCKFIG) over(PARTITION BY i.itemno,i.stockid)) as suma,convert(float,i.STOCKFIG) STOCKFIG  from INVTS01  i
join stits01 s
on i.ITEMNo=s.ITEMNO and i.SUPLNO=s.SUPLNO
where i.INVTNO={invtno} and i.itemno ='{itemno}' order by AVGPR"""