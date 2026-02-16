CREATE OR REPLACE FUNCTION IDENTIFIER(:function_name) (
  query_text STRING COMMENT 'The search term (e.g. "solar charger")',
  filter_category STRING DEFAULT NULL COMMENT 'Optional: Only search within this category.',
  filter_title STRING DEFAULT NULL COMMENT 'Optional: Only search for this specific product name.'
)
RETURNS TABLE (
  id STRING,
  title STRING,
  category STRING,
  description STRING
)
-- The COMMENT tells the Agent exactly how to use this tool
COMMENT 'SEARCH TOOL: Retrieves products using HYBRID search. Use optional filters if the user specifies a category or name.'
RETURN 
  SELECT id, title, category, description 
  FROM vector_search(
    index => "electronics_catalog_dev_aloysiusdjosephaws.electronics_schema.electronics_table_index",
    --index => ${var.table_name}_index,
    query_text => query_text,
    query_type => 'HYBRID',
    num_results => 10 
  )
  WHERE 
    (filter_category IS NULL OR lower(category) = lower(filter_category))
    AND 
    (filter_title IS NULL OR lower(title) = lower(filter_title))
  LIMIT 3;
