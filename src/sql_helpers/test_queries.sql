/***********************************************
-- Using the SQLite database...
************************************************/

-- Find duplicate files is they exist
select 
	filename,
	count(*) as C
from receipts
group by filename 
having C > 1
order by C desc; 
