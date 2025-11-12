import React, { useState } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import api from '../services/api';
import { 
  ChatBubbleLeftRightIcon, 
  SparklesIcon, 
  CheckCircleIcon,
  XCircleIcon,
  ArrowPathIcon,
  LightBulbIcon
} from '@heroicons/react/24/outline';

interface GenieResponse {
  sql: string;
  explanation: string;
  confidence: number;
  conversation_id?: string;
  space_id?: string;
  message_id?: string;
  success: boolean;
  error?: string;
}

interface MetricForm {
  name: string;
  description: string;
  natural_language: string;
  category: string;
}

interface GenieStatus {
  available: boolean;
  message: string;
  configuration: {
    host: boolean;
    token: boolean;
    warehouse: boolean;
  };
}

// (no additional types needed without data context)

const MetricBuilderPage: React.FC = () => {
  const [query, setQuery] = useState('');
  // Data context removed
  const [lastResponse, setLastResponse] = useState<GenieResponse | null>(null);
  const [metricForm, setMetricForm] = useState<MetricForm>({
    name: '',
    description: '',
    natural_language: '',
    category: ''
  });
  const [showMetricForm, setShowMetricForm] = useState(false);

  // Check Genie availability
  const { data: genieStatus } = useQuery<GenieStatus>({
    queryKey: ['genie-status'],
    queryFn: () => api.get('/api/genie/validate-genie').then(res => res.data)
  });

  // Natural language to SQL mutation
  const generateSqlMutation = useMutation<GenieResponse, Error, any>({
    mutationFn: (data: any) => api.post('/api/genie/query', data).then(res => res.data),
    onSuccess: (data: GenieResponse) => {
      setLastResponse(data);
      if (data.success && data.sql) {
        setMetricForm(prev => ({ 
          ...prev, 
          natural_language: query 
        }));
      }
    }
  });

  // Data context removed

  const handleGenerate = () => {
    generateSqlMutation.mutate({ query });
  };

  const handleSaveMetric = async () => {
    if (!lastResponse || !metricForm.name || !metricForm.category) {
      alert('Please fill in all required fields');
      return;
    }

    try {
      const payload = {
        name: metricForm.category, // Use category as the model name
        description: `Semantic model for ${metricForm.category}`,
        category: metricForm.category,
        metric_name: metricForm.name,
        metric_description: metricForm.description,
        natural_language: metricForm.natural_language,
        sql: lastResponse.sql,
        conversation_id: lastResponse.conversation_id,
        message_id: lastResponse.message_id
      };

      const response = await api.post('/api/genie/save-semantic-model', payload);
      
      if (response.data.success) {
        alert(`Metric saved successfully!\n\nModel: ${response.data.model_name}\nFile: ${response.data.file_path}`);
        setShowMetricForm(false);
        // Reset form
        setMetricForm({
          name: '',
          description: '',
          natural_language: '',
          category: ''
        });
      } else {
        alert(`Failed to save metric: ${response.data.error || 'Unknown error'}`);
      }
    } catch (error) {
      console.error('Error saving metric:', error);
      alert('Failed to save metric. Please try again.');
    }
  };

  const confidenceColor = (confidence: number) => {
    if (confidence >= 0.8) return 'text-green-600';
    if (confidence >= 0.6) return 'text-yellow-600';
    return 'text-red-600';
  };

  const confidenceIcon = (confidence: number) => {
    if (confidence >= 0.8) return <CheckCircleIcon className="w-5 h-5 text-green-600" />;
    if (confidence >= 0.6) return <ArrowPathIcon className="w-5 h-5 text-yellow-600" />;
    return <XCircleIcon className="w-5 h-5 text-red-600" />;
  };

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2 flex items-center gap-3">
          <SparklesIcon className="w-8 h-8 text-purple-600" />
          Natural Language Metric Builder
        </h1>
        <p className="text-gray-600">
          Describe your metrics in plain English and let Databricks Genie generate the SQL
        </p>
      </div>

      {/* Genie Status */}
      {genieStatus && (
        <div className={`mb-6 p-4 rounded-lg ${
          genieStatus.available 
            ? 'bg-green-50 border border-green-200' 
            : 'bg-yellow-50 border border-yellow-200'
        }`}>
          <div className="flex items-center gap-2">
            {genieStatus.available ? (
              <>
                <CheckCircleIcon className="w-5 h-5 text-green-600" />
                <span className="text-green-800 font-medium">Databricks Genie is ready</span>
              </>
            ) : (
              <>
                <XCircleIcon className="w-5 h-5 text-yellow-600" />
                <span className="text-yellow-800 font-medium">{genieStatus.message}</span>
              </>
            )}
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left side - Input */}
        <div className="space-y-6">
          {/* Natural Language Input */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <ChatBubbleLeftRightIcon className="w-5 h-5" />
              Describe Your Metric
            </h2>
            
            <textarea
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Example: Calculate total revenue by month for the last year"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500 h-32 resize-none"
            />

            <div className="mt-4 space-y-2">
              <p className="text-sm text-gray-600 font-medium">Try these examples:</p>
              <div className="space-y-1">
                {[
                  "Calculate total revenue by month",
                  "Count unique customers who made purchases last quarter",
                  "Show average order value by product category",
                  "Find month-over-month growth rate of sales",
                  "List top 10 customers by lifetime value"
                ].map((example, idx) => (
                  <button
                    key={idx}
                    onClick={() => setQuery(example)}
                    className="text-sm text-purple-600 hover:text-purple-800 text-left hover:underline flex items-center gap-1"
                  >
                    <LightBulbIcon className="w-4 h-4" />
                    {example}
                  </button>
                ))}
              </div>
            </div>

            <button
              onClick={handleGenerate}
              disabled={!query || generateSqlMutation.isPending}
              className="mt-4 w-full bg-purple-600 text-white py-2 px-4 rounded-md hover:bg-purple-700 disabled:bg-gray-400 transition duration-200 flex items-center justify-center gap-2"
            >
              {generateSqlMutation.isPending ? (
                <>
                  <ArrowPathIcon className="w-5 h-5 animate-spin" />
                  Generating SQL...
                </>
              ) : (
                <>
                  <SparklesIcon className="w-5 h-5" />
                  Generate SQL
                </>
              )}
            </button>
          </div>
        </div>

        {/* Right side - Results */}
        <div className="space-y-6">
          {lastResponse && (
            <>
              {/* Generated SQL */}
              <div className="bg-white rounded-lg shadow p-6">
                <div className="flex justify-between items-start mb-4">
                  <div>
                    <h2 className="text-lg font-semibold">Generated SQL Logic</h2>
                    <p className="text-sm text-gray-600 mt-1">
                      This is the SQL that Databricks Genie would execute
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    {confidenceIcon(lastResponse.confidence)}
                    <span className={`text-sm font-medium ${confidenceColor(lastResponse.confidence)}`}>
                      {Math.round(lastResponse.confidence * 100)}% confidence
                    </span>
                  </div>
                </div>

                {lastResponse.success ? (
                  <>
                    {/* SQL Display */}
                    <div className="space-y-4">
                      <div>
                        <div className="flex items-center justify-between mb-2">
                          <h3 className="text-sm font-semibold text-gray-700">Generated SQL Query:</h3>
                          <span className="bg-purple-600 text-white text-xs px-2 py-1 rounded">
                            SQL LOGIC
                          </span>
                        </div>
                        <pre className="bg-gray-900 text-gray-100 p-4 rounded-md overflow-x-auto text-sm">
                          <code>{lastResponse.sql}</code>
                        </pre>
                      </div>

                      {/* Explanation */}
                      {lastResponse.explanation && (
                        <div>
                          <h3 className="text-sm font-semibold text-gray-700 mb-2">What this query does:</h3>
                          <div className="p-4 bg-blue-50 border-l-4 border-blue-400 rounded-md">
                            <p className="text-sm text-blue-800 whitespace-pre-wrap">{lastResponse.explanation}</p>
                          </div>
                        </div>
                      )}
                    </div>

                    {/* Show Genie conversation details */}
                    {(lastResponse.conversation_id || lastResponse.message_id) && (
                      <div className="mt-4 p-3 bg-gray-50 rounded-md">
                        <p className="text-xs text-gray-600 font-medium mb-1">Genie API Details:</p>
                        <div className="text-xs text-gray-500 space-y-1">
                          {lastResponse.conversation_id && (
                            <div>Conversation ID: <span className="font-mono">{lastResponse.conversation_id}</span></div>
                          )}
                          {lastResponse.message_id && (
                            <div>Message ID: <span className="font-mono">{lastResponse.message_id}</span></div>
                          )}
                          {lastResponse.space_id && (
                            <div>Space ID: <span className="font-mono">{lastResponse.space_id}</span></div>
                          )}
                        </div>
                      </div>
                    )}

                    <button
                      onClick={() => setShowMetricForm(true)}
                      className="mt-4 w-full bg-green-600 text-white py-2 px-4 rounded-md hover:bg-green-700 transition duration-200"
                    >
                      Save as Metric
                    </button>
                  </>
                ) : (
                  <div className="p-4 bg-red-50 rounded-md">
                    <p className="text-red-800">{lastResponse.error || 'Failed to generate SQL'}</p>
                  </div>
                )}
              </div>

              {/* Metric Form */}
              {showMetricForm && lastResponse.success && (
                <div className="bg-white rounded-lg shadow p-6">
                  <h2 className="text-lg font-semibold mb-4">Save as Reusable Metric</h2>
                  
                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Metric Name
                      </label>
                      <input
                        type="text"
                        value={metricForm.name}
                        onChange={(e) => setMetricForm(prev => ({ ...prev, name: e.target.value }))}
                        placeholder="e.g., monthly_revenue"
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Description
                      </label>
                      <input
                        type="text"
                        value={metricForm.description}
                        onChange={(e) => setMetricForm(prev => ({ ...prev, description: e.target.value }))}
                        placeholder="e.g., Total revenue grouped by month"
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Category
                      </label>
                      <input
                        type="text"
                        value={metricForm.category}
                        onChange={(e) => setMetricForm(prev => ({ ...prev, category: e.target.value }))}
                        placeholder="e.g., sales_metrics, customer_analytics"
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500"
                      />
                    </div>

                    <div className="flex gap-3">
                      <button
                        onClick={handleSaveMetric}
                        className="flex-1 bg-green-600 text-white py-2 px-4 rounded-md hover:bg-green-700 transition duration-200"
                      >
                        Save Metric
                      </button>
                      <button
                        onClick={() => setShowMetricForm(false)}
                        className="flex-1 bg-gray-300 text-gray-700 py-2 px-4 rounded-md hover:bg-gray-400 transition duration-200"
                      >
                        Cancel
                      </button>
                    </div>
                  </div>
                </div>
              )}
            </>
          )}

          {/* Placeholder when no results */}
          {!lastResponse && (
            <div className="bg-gray-50 rounded-lg p-12 text-center">
              <SparklesIcon className="w-16 h-16 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-600">
                Describe a metric in natural language and click "Generate SQL" to see the magic!
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default MetricBuilderPage;
