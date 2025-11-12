import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { getCatalogs, getSchemas, getTables, getColumns } from '../services/api';
import { 
  ChevronRightIcon, 
  ChevronDownIcon, 
  CircleStackIcon,
  TableCellsIcon,
  RectangleStackIcon,
  DocumentIcon,
  InformationCircleIcon
} from '@heroicons/react/24/outline';

function MetadataPage() {
  const [expandedCatalogs, setExpandedCatalogs] = useState<Set<string>>(new Set());
  const [expandedSchemas, setExpandedSchemas] = useState<Set<string>>(new Set());
  const [expandedTables, setExpandedTables] = useState<Set<string>>(new Set());
  const [selectedTable, setSelectedTable] = useState<{ catalog: string; schema: string; table: string } | null>(null);

  const { data: catalogs, isLoading: catalogsLoading } = useQuery({
    queryKey: ['catalogs'],
    queryFn: getCatalogs,
    enabled: true,
  });

  const toggleCatalog = (catalog: string) => {
    const newExpanded = new Set(expandedCatalogs);
    if (newExpanded.has(catalog)) {
      newExpanded.delete(catalog);
    } else {
      newExpanded.add(catalog);
    }
    setExpandedCatalogs(newExpanded);
  };

  const toggleSchema = (catalogSchema: string) => {
    const newExpanded = new Set(expandedSchemas);
    if (newExpanded.has(catalogSchema)) {
      newExpanded.delete(catalogSchema);
    } else {
      newExpanded.add(catalogSchema);
    }
    setExpandedSchemas(newExpanded);
  };

  const toggleTable = (catalogSchemaTable: string) => {
    const newExpanded = new Set(expandedTables);
    if (newExpanded.has(catalogSchemaTable)) {
      newExpanded.delete(catalogSchemaTable);
    } else {
      newExpanded.add(catalogSchemaTable);
    }
    setExpandedTables(newExpanded);
  };

  // Tree component for catalog schemas
  const CatalogSchemas = ({ catalog }: { catalog: string }) => {
    const { data: schemas, isLoading } = useQuery({
      queryKey: ['schemas', catalog],
      queryFn: () => getSchemas(catalog),
      enabled: expandedCatalogs.has(catalog),
    });

    if (!expandedCatalogs.has(catalog)) return null;

    // Debug log
    console.log('CatalogSchemas - catalog:', catalog, 'schemas:', schemas, 'isLoading:', isLoading);

    return (
      <div className="ml-6 mt-2">
        {isLoading ? (
          <div className="text-sm text-gray-500">Loading schemas...</div>
        ) : schemas && schemas.length > 0 ? (
          schemas.map((schema: string) => (
            <div key={schema} className="mb-2">
              <div
                className="flex items-center cursor-pointer hover:bg-gray-50 p-2 rounded"
                onClick={() => toggleSchema(`${catalog}.${schema}`)}
              >
                {expandedSchemas.has(`${catalog}.${schema}`) ? (
                  <ChevronDownIcon className="h-4 w-4 text-gray-400 mr-2" />
                ) : (
                  <ChevronRightIcon className="h-4 w-4 text-gray-400 mr-2" />
                )}
                <RectangleStackIcon className="h-4 w-4 text-green-500 mr-2" />
                <span className="text-sm font-medium text-gray-700">{schema}</span>
              </div>
              <SchemaTables catalog={catalog} schema={schema} />
            </div>
          ))
        ) : (
          <div className="text-sm text-gray-500 ml-6">No schemas found</div>
        )}
      </div>
    );
  };

  // Tree component for schema tables
  const SchemaTables = ({ catalog, schema }: { catalog: string; schema: string }) => {
    const { data: tables, isLoading } = useQuery({
      queryKey: ['tables', catalog, schema],
      queryFn: () => getTables(catalog, schema),
      enabled: expandedSchemas.has(`${catalog}.${schema}`),
    });

    if (!expandedSchemas.has(`${catalog}.${schema}`)) return null;

    return (
      <div className="ml-6 mt-2">
        {isLoading ? (
          <div className="text-sm text-gray-500">Loading tables...</div>
        ) : tables && tables.length > 0 ? (
          tables.map((table: any) => (
            <div key={table.name} className="mb-2">
              <div
                className="flex items-center cursor-pointer hover:bg-gray-50 p-2 rounded"
                onClick={() => {
                  toggleTable(`${catalog}.${schema}.${table.name}`);
                  setSelectedTable({ catalog, schema, table: table.name });
                }}
              >
                {expandedTables.has(`${catalog}.${schema}.${table.name}`) ? (
                  <ChevronDownIcon className="h-4 w-4 text-gray-400 mr-2" />
                ) : (
                  <ChevronRightIcon className="h-4 w-4 text-gray-400 mr-2" />
                )}
                <TableCellsIcon className="h-4 w-4 text-blue-500 mr-2" />
                <div className="flex-1">
                  <div className="text-sm font-medium text-gray-700">{table.name}</div>
                  <div className="text-xs text-gray-500 uppercase">{table.table_type || table.type}</div>
                </div>
              </div>
              <TableColumns catalog={catalog} schema={schema} table={table.name} />
            </div>
          ))
        ) : (
          <div className="text-sm text-gray-500 ml-6">No tables found</div>
        )}
      </div>
    );
  };

  // Tree component for table columns
  const TableColumns = ({ catalog, schema, table }: { catalog: string; schema: string; table: string }) => {
    const { data: columns, isLoading } = useQuery({
      queryKey: ['columns', catalog, schema, table],
      queryFn: () => getColumns(catalog, schema, table),
      enabled: expandedTables.has(`${catalog}.${schema}.${table}`),
    });

    if (!expandedTables.has(`${catalog}.${schema}.${table}`)) return null;

    return (
      <div className="ml-6 mt-2 bg-gray-50 rounded-lg p-3">
        {isLoading ? (
          <div className="text-sm text-gray-500">Loading columns...</div>
        ) : columns && columns.length > 0 ? (
          <div className="space-y-2">
            {columns.map((column: any, idx: number) => (
              <div key={idx} className="flex items-start space-x-2 p-2 bg-white rounded border">
                <DocumentIcon className="h-4 w-4 text-purple-500 mt-0.5 flex-shrink-0" />
                <div className="flex-1 min-w-0">
                  <div className="flex items-center space-x-2">
                    <span className="font-medium text-gray-900">{column.name}</span>
                    <span className="text-xs bg-gray-100 text-gray-700 px-2 py-1 rounded">
                      {column.data_type}
                    </span>
                    {!column.is_nullable && (
                      <span className="text-xs bg-red-100 text-red-700 px-2 py-1 rounded">
                        NOT NULL
                      </span>
                    )}
                  </div>
                  {column.comment && (
                    <div className="text-xs text-gray-500 mt-1">{column.comment}</div>
                  )}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-sm text-gray-500">No columns found</div>
        )}
      </div>
    );
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900">Metadata Explorer</h2>
        <p className="mt-2 text-gray-600">
          Browse tables and columns in your Databricks Unity Catalog
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Tree View */}
        <div className="lg:col-span-2 bg-white shadow rounded-lg p-6">
          <div className="flex items-center mb-4">
            <CircleStackIcon className="h-5 w-5 text-gray-500 mr-2" />
            <h3 className="text-lg font-medium text-gray-900">Database Catalog</h3>
          </div>
          
          <div className="space-y-1 max-h-[70vh] overflow-y-auto">
            {catalogsLoading ? (
              <div className="text-gray-500">Loading catalogs...</div>
            ) : catalogs && catalogs.length > 0 ? (
              catalogs.map((catalog: any) => (
                <div key={catalog.name || catalog} className="mb-2">
                  <div
                    className="flex items-center cursor-pointer hover:bg-gray-50 p-2 rounded"
                    onClick={() => toggleCatalog(catalog.name || catalog)}
                  >
                    {expandedCatalogs.has(catalog.name || catalog) ? (
                      <ChevronDownIcon className="h-4 w-4 text-gray-400 mr-2" />
                    ) : (
                      <ChevronRightIcon className="h-4 w-4 text-gray-400 mr-2" />
                    )}
                    <CircleStackIcon className="h-4 w-4 text-indigo-500 mr-2" />
                    <span className="font-medium text-gray-900">{catalog.name || catalog}</span>
                  </div>
                  <CatalogSchemas catalog={catalog.name || catalog} />
                </div>
              ))
            ) : (
              <div className="text-gray-500">No catalogs found</div>
            )}
          </div>
        </div>

        {/* Table Details Panel */}
        <div className="bg-white shadow rounded-lg p-6">
          <div className="flex items-center mb-4">
            <InformationCircleIcon className="h-5 w-5 text-gray-500 mr-2" />
            <h3 className="text-lg font-medium text-gray-900">Table Details</h3>
          </div>
          
          {selectedTable ? (
            <div className="space-y-4">
              <div>
                <label className="text-sm font-medium text-gray-500">Full Qualified Name</label>
                <div className="mt-1 p-3 bg-gray-50 rounded-lg">
                  <code className="text-sm font-mono text-gray-900 break-all">
                    {selectedTable.catalog}.{selectedTable.schema}.{selectedTable.table}
                  </code>
                </div>
              </div>
              
              <div>
                <label className="text-sm font-medium text-gray-500">Catalog</label>
                <div className="mt-1 text-sm text-gray-900">{selectedTable.catalog}</div>
              </div>
              
              <div>
                <label className="text-sm font-medium text-gray-500">Schema</label>
                <div className="mt-1 text-sm text-gray-900">{selectedTable.schema}</div>
              </div>
              
              <div>
                <label className="text-sm font-medium text-gray-500">Table</label>
                <div className="mt-1 text-sm text-gray-900">{selectedTable.table}</div>
              </div>
              
              <div className="pt-4 border-t">
                <button
                  onClick={() => {
                    const fullName = `${selectedTable.catalog}.${selectedTable.schema}.${selectedTable.table}`;
                    navigator.clipboard.writeText(fullName);
                  }}
                  className="w-full bg-blue-600 text-white text-sm px-4 py-2 rounded-md hover:bg-blue-700 transition-colors"
                >
                  Copy Full Name
                </button>
              </div>
            </div>
          ) : (
            <div className="text-center py-8">
              <TableCellsIcon className="h-12 w-12 text-gray-300 mx-auto mb-3" />
              <p className="text-gray-500">Select a table to view details</p>
              <p className="text-sm text-gray-400 mt-1">
                Click on any table in the tree to see its details
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default MetadataPage;