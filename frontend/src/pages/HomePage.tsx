import React from 'react';
import { Link } from 'react-router-dom';
import {
  ChartBarIcon,
  CircleStackIcon,
  BeakerIcon,
  CubeIcon,
  WrenchIcon,
  SparklesIcon,
  DocumentTextIcon,
  ShareIcon,
  ArrowRightIcon,
  RocketLaunchIcon,
  LightBulbIcon,
  CpuChipIcon
} from '@heroicons/react/24/outline';

function HomePage() {
  return (
    <div className="max-w-7xl mx-auto space-y-8">
      {/* Hero Section */}
      <div className="text-center mb-12">
        <div className="flex justify-center mb-6">
          <div className="p-4 bg-gradient-to-br from-gray-100 to-gray-200 dark:from-gray-700 dark:to-gray-800 rounded-2xl">
            <RocketLaunchIcon className="h-16 w-16 text-gray-900 dark:text-white" />
          </div>
        </div>
        <h1 className="text-5xl font-bold text-gray-900 dark:text-white tracking-tight mb-4">
          Semantic Layer Platform
        </h1>
        <p className="text-xl text-gray-600 dark:text-gray-300 max-w-3xl mx-auto leading-relaxed">
          Your unified platform for managing metrics, exploring data, and building semantic models 
          with AI-powered insights on Databricks
        </p>
      </div>

      {/* User Journeys */}
      <div className="mb-12">
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-6 flex items-center">
          <LightBulbIcon className="h-8 w-8 text-yellow-500 dark:text-yellow-400 mr-2" />
          Choose Your Journey
        </h2>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Data Analyst Journey */}
          <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl p-6 hover:shadow-lg dark:hover:shadow-gray-800/50 transition-shadow">
            <div className="flex items-center mb-4">
              <div className="p-2 bg-blue-100 dark:bg-blue-900/30 rounded-lg">
                <ChartBarIcon className="h-6 w-6 text-blue-600 dark:text-blue-400" />
              </div>
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white ml-3">Data Analyst</h3>
            </div>
            <p className="text-gray-600 dark:text-gray-300 text-sm mb-4">
              Explore metrics, analyze data, and create insightful reports
            </p>
            <div className="space-y-2">
              <Link to="/metrics" className="flex items-center text-sm text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-300">
                <ArrowRightIcon className="h-4 w-4 mr-1" />
                Explore Metrics
              </Link>
              <Link to="/query" className="flex items-center text-sm text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-300">
                <ArrowRightIcon className="h-4 w-4 mr-1" />
                Query Lab
              </Link>
              <Link to="/lineage" className="flex items-center text-sm text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-300">
                <ArrowRightIcon className="h-4 w-4 mr-1" />
                Data Lineage
              </Link>
            </div>
          </div>

          {/* Data Engineer Journey */}
          <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl p-6 hover:shadow-lg dark:hover:shadow-gray-800/50 transition-shadow">
            <div className="flex items-center mb-4">
              <div className="p-2 bg-green-100 dark:bg-green-900/30 rounded-lg">
                <CpuChipIcon className="h-6 w-6 text-green-600 dark:text-green-400" />
              </div>
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white ml-3">Data Engineer</h3>
            </div>
            <p className="text-gray-600 dark:text-gray-300 text-sm mb-4">
              Build semantic models, manage metadata, and optimize performance
            </p>
            <div className="space-y-2">
              <Link to="/models" className="flex items-center text-sm text-green-600 dark:text-green-400 hover:text-green-800 dark:hover:text-green-300">
                <ArrowRightIcon className="h-4 w-4 mr-1" />
                Semantic Models
              </Link>
              <Link to="/metadata" className="flex items-center text-sm text-green-600 dark:text-green-400 hover:text-green-800 dark:hover:text-green-300">
                <ArrowRightIcon className="h-4 w-4 mr-1" />
                Metadata Explorer
              </Link>
              <Link to="/metric-builder" className="flex items-center text-sm text-green-600 dark:text-green-400 hover:text-green-800 dark:hover:text-green-300">
                <ArrowRightIcon className="h-4 w-4 mr-1" />
                Metric Builder
              </Link>
            </div>
          </div>

          {/* Business User Journey */}
          <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl p-6 hover:shadow-lg dark:hover:shadow-gray-800/50 transition-shadow">
            <div className="flex items-center mb-4">
              <div className="p-2 bg-purple-100 dark:bg-purple-900/30 rounded-lg">
                <DocumentTextIcon className="h-6 w-6 text-purple-600 dark:text-purple-400" />
              </div>
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white ml-3">Business User</h3>
            </div>
            <p className="text-gray-600 dark:text-gray-300 text-sm mb-4">
              Access documentation and leverage AI-powered insights
            </p>
            <div className="space-y-2">
              <Link to="/documentation" className="flex items-center text-sm text-purple-600 dark:text-purple-400 hover:text-purple-800 dark:hover:text-purple-300">
                <ArrowRightIcon className="h-4 w-4 mr-1" />
                Documentation
              </Link>
              <Link to="/auto-generate" className="flex items-center text-sm text-purple-600 dark:text-purple-400 hover:text-purple-800 dark:hover:text-purple-300">
                <ArrowRightIcon className="h-4 w-4 mr-1" />
                AI Model Generation
              </Link>
              <Link to="/metrics" className="flex items-center text-sm text-purple-600 dark:text-purple-400 hover:text-purple-800 dark:hover:text-purple-300">
                <ArrowRightIcon className="h-4 w-4 mr-1" />
                Browse Metrics
              </Link>
            </div>
          </div>
        </div>
      </div>

      {/* Feature Cards */}
      <div>
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-6 flex items-center">
          <CpuChipIcon className="h-8 w-8 text-gray-700 dark:text-gray-300 mr-2" />
          Platform Capabilities
        </h2>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {/* Metrics Explorer */}
          <Link to="/metrics" className="group">
            <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl p-6 h-full hover:border-gray-300 dark:hover:border-gray-600 hover:shadow-md dark:hover:shadow-gray-800/50 transition-all">
              <ChartBarIcon className="h-10 w-10 text-gray-700 dark:text-gray-300 mb-4 group-hover:text-gray-900 dark:group-hover:text-white" />
              <h3 className="font-semibold text-gray-900 dark:text-white mb-2">Metrics Explorer</h3>
              <p className="text-sm text-gray-600 dark:text-gray-300">
                Browse and analyze all available metrics with filtering and categorization
              </p>
            </div>
          </Link>

          {/* Metadata Explorer */}
          <Link to="/metadata" className="group">
            <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl p-6 h-full hover:border-gray-300 dark:hover:border-gray-600 hover:shadow-md dark:hover:shadow-gray-800/50 transition-all">
              <CircleStackIcon className="h-10 w-10 text-gray-700 dark:text-gray-300 mb-4 group-hover:text-gray-900 dark:group-hover:text-white" />
              <h3 className="font-semibold text-gray-900 dark:text-white mb-2">Metadata Explorer</h3>
              <p className="text-sm text-gray-600 dark:text-gray-300">
                Navigate catalogs, schemas, and tables in your Databricks workspace
              </p>
            </div>
          </Link>

          {/* Query Lab */}
          <Link to="/query" className="group">
            <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl p-6 h-full hover:border-gray-300 dark:hover:border-gray-600 hover:shadow-md dark:hover:shadow-gray-800/50 transition-all">
              <BeakerIcon className="h-10 w-10 text-gray-700 dark:text-gray-300 mb-4 group-hover:text-gray-900 dark:group-hover:text-white" />
              <h3 className="font-semibold text-gray-900 dark:text-white mb-2">Query Lab</h3>
              <p className="text-sm text-gray-600 dark:text-gray-300">
                Execute SQL queries with intelligent autocomplete and result visualization
              </p>
            </div>
          </Link>

          {/* Semantic Models */}
          <Link to="/models" className="group">
            <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl p-6 h-full hover:border-gray-300 dark:hover:border-gray-600 hover:shadow-md dark:hover:shadow-gray-800/50 transition-all">
              <CubeIcon className="h-10 w-10 text-gray-700 dark:text-gray-300 mb-4 group-hover:text-gray-900 dark:group-hover:text-white" />
              <h3 className="font-semibold text-gray-900 dark:text-white mb-2">Semantic Models</h3>
              <p className="text-sm text-gray-600 dark:text-gray-300">
                Define and manage semantic models with entities, measures, and dimensions
              </p>
            </div>
          </Link>

          {/* Metric Builder */}
          <Link to="/metric-builder" className="group">
            <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl p-6 h-full hover:border-gray-300 dark:hover:border-gray-600 hover:shadow-md dark:hover:shadow-gray-800/50 transition-all">
              <WrenchIcon className="h-10 w-10 text-gray-700 dark:text-gray-300 mb-4 group-hover:text-gray-900 dark:group-hover:text-white" />
              <h3 className="font-semibold text-gray-900 dark:text-white mb-2">Metric Builder</h3>
              <p className="text-sm text-gray-600 dark:text-gray-300">
                Create custom business metrics with SQL or visual builders
              </p>
            </div>
          </Link>

          {/* Auto Generate */}
          <Link to="/auto-generate" className="group">
            <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl p-6 h-full hover:border-gray-300 dark:hover:border-gray-600 hover:shadow-md dark:hover:shadow-gray-800/50 transition-all">
              <SparklesIcon className="h-10 w-10 text-gray-700 dark:text-gray-300 mb-4 group-hover:text-gray-900 dark:group-hover:text-white" />
              <h3 className="font-semibold text-gray-900 dark:text-white mb-2">AI Generation</h3>
              <p className="text-sm text-gray-600 dark:text-gray-300">
                Use AI to automatically generate semantic models from your tables
              </p>
            </div>
          </Link>

          {/* Documentation */}
          <Link to="/documentation" className="group">
            <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl p-6 h-full hover:border-gray-300 dark:hover:border-gray-600 hover:shadow-md dark:hover:shadow-gray-800/50 transition-all">
              <DocumentTextIcon className="h-10 w-10 text-gray-700 dark:text-gray-300 mb-4 group-hover:text-gray-900 dark:group-hover:text-white" />
              <h3 className="font-semibold text-gray-900 dark:text-white mb-2">Documentation</h3>
              <p className="text-sm text-gray-600 dark:text-gray-300">
                Generate comprehensive documentation for your semantic models
              </p>
            </div>
          </Link>

          {/* Lineage */}
          <Link to="/lineage" className="group">
            <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl p-6 h-full hover:border-gray-300 dark:hover:border-gray-600 hover:shadow-md dark:hover:shadow-gray-800/50 transition-all">
              <ShareIcon className="h-10 w-10 text-gray-700 dark:text-gray-300 mb-4 group-hover:text-gray-900 dark:group-hover:text-white" />
              <h3 className="font-semibold text-gray-900 dark:text-white mb-2">Data Lineage</h3>
              <p className="text-sm text-gray-600 dark:text-gray-300">
                Visualize data flow and dependencies across your data platform
              </p>
            </div>
          </Link>
        </div>
      </div>

      {/* Quick Start */}
      <div className="bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl p-8 mt-12">
        <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-6">Getting Started</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          <div>
            <h4 className="font-semibold text-gray-900 dark:text-white mb-3">Configure Databricks Connection</h4>
            <pre className="p-4 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg text-xs text-gray-800 dark:text-gray-200 overflow-x-auto">
{`DATABRICKS_HOST=your-workspace.cloud.databricks.com
DATABRICKS_TOKEN=your-personal-access-token
DATABRICKS_HTTP_PATH=/sql/1.0/warehouses/your-warehouse-id`}
            </pre>
          </div>
          <div>
            <h4 className="font-semibold text-gray-900 dark:text-white mb-3">Start Exploring</h4>
            <ol className="space-y-2 text-sm text-gray-600 dark:text-gray-300">
              <li className="flex items-start">
                <span className="font-medium text-gray-900 dark:text-white mr-2">1.</span>
                Check connection status in the sidebar
              </li>
              <li className="flex items-start">
                <span className="font-medium text-gray-900 dark:text-white mr-2">2.</span>
                Browse available metrics in Metrics Explorer
              </li>
              <li className="flex items-start">
                <span className="font-medium text-gray-900 dark:text-white mr-2">3.</span>
                Create your first semantic model
              </li>
              <li className="flex items-start">
                <span className="font-medium text-gray-900 dark:text-white mr-2">4.</span>
                Generate documentation with AI
              </li>
            </ol>
          </div>
        </div>
      </div>
    </div>
  );
}

export default HomePage;
