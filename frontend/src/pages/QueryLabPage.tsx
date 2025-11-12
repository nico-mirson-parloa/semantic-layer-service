import React, { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { executeQuery, validateQuery } from '../services/api';
import { SQLEditor } from '../components/SQLEditor';

function QueryLabPage() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<any>(null);

  const executeMutation = useMutation({
    mutationFn: executeQuery,
    onSuccess: (data) => {
      setResults(data);
    },
  });

  const validateMutation = useMutation({
    mutationFn: validateQuery,
  });

  const handleExecute = () => {
    if (query.trim()) {
      executeMutation.mutate({ query });
    }
  };

  const handleValidate = () => {
    if (query.trim()) {
      validateMutation.mutate({ query });
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900">Query Lab</h2>
        <p className="mt-2 text-gray-600">
          Execute SQL queries against your Databricks SQL Warehouse
        </p>
      </div>

      {/* Query Editor */}
      <div className="bg-white shadow rounded-lg p-6">
        <div className="space-y-4">
          <div>
            <label htmlFor="query" className="block text-sm font-medium text-gray-700 mb-2">
              SQL Query
            </label>
            <SQLEditor
              value={query}
              onChange={setQuery}
              onExecute={handleExecute}
            />
          </div>

          <div className="flex space-x-4">
            <button
              onClick={handleExecute}
              disabled={!query.trim() || executeMutation.isPending}
              className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
            >
              {executeMutation.isPending ? 'Executing...' : 'Execute Query'}
            </button>

            <button
              onClick={handleValidate}
              disabled={!query.trim() || validateMutation.isPending}
              className="inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
            >
              {validateMutation.isPending ? 'Validating...' : 'Validate'}
            </button>
          </div>

          {/* Validation Result */}
          {validateMutation.data && (
            <div
              className={`p-4 rounded-md ${
                validateMutation.data.valid
                  ? 'bg-green-50 text-green-800'
                  : 'bg-red-50 text-red-800'
              }`}
            >
              <p className="text-sm">{validateMutation.data.message}</p>
            </div>
          )}
        </div>
      </div>

      {/* Query Results */}
      {results && (
        <div className="bg-white shadow rounded-lg p-6">
          <div className="mb-4">
            <h3 className="text-lg font-medium text-gray-900">Results</h3>
            <div className="mt-2 flex space-x-4 text-sm text-gray-500">
              <span>{results.row_count} rows</span>
              <span>{results.execution_time.toFixed(2)}s</span>
            </div>
          </div>

          {results.success ? (
            results.data.length > 0 ? (
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      {results.columns.map((column: string) => (
                        <th
                          key={column}
                          className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                        >
                          {column}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {results.data.map((row: any, idx: number) => (
                      <tr key={idx}>
                        {results.columns.map((column: string) => (
                          <td
                            key={column}
                            className="px-6 py-4 whitespace-nowrap text-sm text-gray-900"
                          >
                            {row[column] !== null ? String(row[column]) : 'NULL'}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <p className="text-gray-500">No results returned</p>
            )
          ) : (
            <div className="p-4 bg-red-50 rounded-md">
              <p className="text-sm text-red-800">Error: {results.error}</p>
            </div>
          )}
        </div>
      )}

      {/* Error Display */}
      {executeMutation.isError && (
        <div className="bg-red-50 border border-red-200 rounded-md p-4">
          <p className="text-sm text-red-800">
            {executeMutation.error?.message || 'An error occurred'}
          </p>
        </div>
      )}
    </div>
  );
}

export default QueryLabPage;
