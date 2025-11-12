import React, { useState } from 'react';
import { Dialog, Transition } from '@headlessui/react';
import { Fragment } from 'react';
import { XMarkIcon, PencilIcon, ArrowDownTrayIcon, CheckIcon, XCircleIcon } from '@heroicons/react/24/outline';
import { 
  CubeIcon, 
  ChartBarIcon, 
  CalculatorIcon,
  ClockIcon,
  TagIcon,
  CodeBracketIcon 
} from '@heroicons/react/24/outline';
import { downloadModel, updateModel } from '../services/api';

interface ModelDetails {
  id: string;
  raw: any;
  parsed?: any;
  file_path: string;
  raw_yaml?: string;
}

interface ModelDetailModalProps {
  isOpen: boolean;
  onClose: () => void;
  model: ModelDetails | null;
  onModelUpdated?: () => void;
}

function ModelDetailModal({ isOpen, onClose, model, onModelUpdated }: ModelDetailModalProps) {
  const [isEditing, setIsEditing] = useState(false);
  const [editedYaml, setEditedYaml] = useState('');
  const [isSaving, setIsSaving] = useState(false);
  const [saveError, setSaveError] = useState('');

  if (!model) return null;

  const modelData = model.raw?.semantic_model || model.raw || {};

  const handleEditClick = () => {
    setEditedYaml(model.raw_yaml || JSON.stringify(modelData, null, 2));
    setIsEditing(true);
    setSaveError('');
  };

  const handleCancelEdit = () => {
    setIsEditing(false);
    setEditedYaml('');
    setSaveError('');
  };

  const handleSaveEdit = async () => {
    setIsSaving(true);
    setSaveError('');
    
    try {
      await updateModel(model.id, editedYaml);
      setIsEditing(false);
      setEditedYaml('');
      onModelUpdated?.();
    } catch (error: any) {
      setSaveError(error.response?.data?.detail || 'Failed to save changes');
    } finally {
      setIsSaving(false);
    }
  };

  const handleDownload = async () => {
    try {
      await downloadModel(model.id);
    } catch (error) {
      console.error('Failed to download model:', error);
    }
  };

  return (
    <Transition appear show={isOpen} as={Fragment}>
      <Dialog as="div" className="relative z-10" onClose={onClose}>
        <Transition.Child
          as={Fragment}
          enter="ease-out duration-300"
          enterFrom="opacity-0"
          enterTo="opacity-100"
          leave="ease-in duration-200"
          leaveFrom="opacity-100"
          leaveTo="opacity-0"
        >
          <div className="fixed inset-0 bg-black bg-opacity-25" />
        </Transition.Child>

        <div className="fixed inset-0 overflow-y-auto">
          <div className="flex min-h-full items-center justify-center p-4 text-center">
            <Transition.Child
              as={Fragment}
              enter="ease-out duration-300"
              enterFrom="opacity-0 scale-95"
              enterTo="opacity-100 scale-100"
              leave="ease-in duration-200"
              leaveFrom="opacity-100 scale-100"
              leaveTo="opacity-0 scale-95"
            >
              <Dialog.Panel className="w-full max-w-4xl transform overflow-hidden rounded-2xl bg-white p-6 text-left align-middle shadow-xl transition-all">
                <Dialog.Title
                  as="div"
                  className="flex items-center justify-between border-b pb-4"
                >
                  <div>
                    <h3 className="text-2xl font-semibold leading-6 text-gray-900">
                      {modelData.name || model.id}
                    </h3>
                    {modelData.description && (
                      <p className="mt-2 text-sm text-gray-600">{modelData.description}</p>
                    )}
                  </div>
                  <div className="flex items-center space-x-2">
                    <button
                      type="button"
                      className="inline-flex items-center rounded-md bg-blue-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-blue-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-600"
                      onClick={handleDownload}
                    >
                      <ArrowDownTrayIcon className="h-4 w-4 mr-1" />
                      Download
                    </button>
                    <button
                      type="button"
                      className="inline-flex items-center rounded-md bg-green-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-green-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-green-600"
                      onClick={handleEditClick}
                    >
                      <PencilIcon className="h-4 w-4 mr-1" />
                      Edit
                    </button>
                    <button
                      type="button"
                      className="rounded-md bg-white text-gray-400 hover:text-gray-500 focus:outline-none focus:ring-2 focus:ring-gray-500"
                      onClick={onClose}
                    >
                      <span className="sr-only">Close</span>
                      <XMarkIcon className="h-6 w-6" aria-hidden="true" />
                    </button>
                  </div>
                </Dialog.Title>

                <div className="mt-6 space-y-6 max-h-[70vh] overflow-y-auto">
                  {/* Model Reference */}
                  {modelData.model && (
                    <div className="bg-gray-50 rounded-lg p-4">
                      <h4 className="text-sm font-medium text-gray-900 mb-2">Base Model</h4>
                      <code className="text-sm bg-gray-100 px-2 py-1 rounded">
                        {modelData.model}
                      </code>
                    </div>
                  )}

                  {/* Entities */}
                  {modelData.entities && modelData.entities.length > 0 && (
                    <div>
                      <h4 className="text-lg font-medium text-gray-900 mb-3 flex items-center">
                        <CubeIcon className="h-5 w-5 mr-2 text-blue-500" />
                        Entities
                      </h4>
                      <div className="space-y-2">
                        {modelData.entities.map((entity: any, idx: number) => (
                          <div key={idx} className="bg-blue-50 rounded-lg p-3">
                            <div className="flex items-center justify-between">
                              <span className="font-medium">{entity.name}</span>
                              <span className="text-sm text-blue-600 bg-blue-100 px-2 py-1 rounded">
                                {entity.type}
                              </span>
                            </div>
                            <code className="text-sm text-gray-600 mt-1 block">
                              expr: {entity.expr}
                            </code>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Dimensions */}
                  {modelData.dimensions && modelData.dimensions.length > 0 && (
                    <div>
                      <h4 className="text-lg font-medium text-gray-900 mb-3 flex items-center">
                        <TagIcon className="h-5 w-5 mr-2 text-green-500" />
                        Dimensions
                      </h4>
                      <div className="space-y-2">
                        {modelData.dimensions.map((dim: any, idx: number) => (
                          <div key={idx} className="bg-green-50 rounded-lg p-3">
                            <div className="flex items-center justify-between">
                              <span className="font-medium">{dim.name}</span>
                              <div className="flex items-center space-x-2">
                                <span className="text-sm text-green-600 bg-green-100 px-2 py-1 rounded">
                                  {dim.type}
                                </span>
                                {dim.type === 'time' && <ClockIcon className="h-4 w-4 text-green-600" />}
                              </div>
                            </div>
                            <code className="text-sm text-gray-600 mt-1 block">
                              expr: {dim.expr}
                            </code>
                            {dim.time_granularity && (
                              <div className="mt-2 flex flex-wrap gap-1">
                                {dim.time_granularity.map((gran: string) => (
                                  <span key={gran} className="text-xs bg-gray-200 px-2 py-1 rounded">
                                    {gran}
                                  </span>
                                ))}
                              </div>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Measures */}
                  {modelData.measures && modelData.measures.length > 0 && (
                    <div>
                      <h4 className="text-lg font-medium text-gray-900 mb-3 flex items-center">
                        <CalculatorIcon className="h-5 w-5 mr-2 text-purple-500" />
                        Measures
                      </h4>
                      <div className="space-y-2">
                        {modelData.measures.map((measure: any, idx: number) => (
                          <div key={idx} className="bg-purple-50 rounded-lg p-3">
                            <div className="flex items-center justify-between">
                              <span className="font-medium">{measure.name}</span>
                              <span className="text-sm text-purple-600 bg-purple-100 px-2 py-1 rounded">
                                {measure.agg}
                              </span>
                            </div>
                            <code className="text-sm text-gray-600 mt-1 block">
                              expr: {measure.expr}
                            </code>
                            {measure.description && (
                              <p className="text-sm text-gray-500 mt-1">{measure.description}</p>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Metrics */}
                  {modelData.metrics && modelData.metrics.length > 0 && (
                    <div>
                      <h4 className="text-lg font-medium text-gray-900 mb-3 flex items-center">
                        <ChartBarIcon className="h-5 w-5 mr-2 text-orange-500" />
                        Metrics
                      </h4>
                      <div className="space-y-3">
                        {modelData.metrics.map((metric: any, idx: number) => (
                          <div key={idx} className="bg-orange-50 rounded-lg p-4">
                            <div className="flex items-center justify-between">
                              <span className="font-medium text-lg">{metric.name}</span>
                              <span className="text-sm text-orange-600 bg-orange-100 px-2 py-1 rounded">
                                {metric.type}
                              </span>
                            </div>
                            {metric.description && (
                              <p className="text-sm text-gray-600 mt-2">{metric.description}</p>
                            )}
                            {metric.measure && (
                              <div className="mt-2">
                                <span className="text-sm text-gray-500">Measure: </span>
                                <code className="text-sm bg-gray-100 px-2 py-1 rounded">
                                  {metric.measure}
                                </code>
                              </div>
                            )}
                            {metric.sql && (
                              <div className="mt-3">
                                <div className="flex items-center mb-2">
                                  <CodeBracketIcon className="h-4 w-4 mr-1 text-gray-500" />
                                  <span className="text-sm font-medium text-gray-700">Generated SQL:</span>
                                </div>
                                <pre className="text-xs bg-gray-900 text-gray-100 p-3 rounded overflow-x-auto">
                                  {metric.sql}
                                </pre>
                              </div>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Metadata */}
                  {modelData.metadata && (
                    <div>
                      <h4 className="text-lg font-medium text-gray-900 mb-3">Metadata</h4>
                      <div className="bg-gray-50 rounded-lg p-4 space-y-2">
                        {modelData.metadata.category && (
                          <div>
                            <span className="text-sm font-medium text-gray-600">Category: </span>
                            <span className="text-sm text-gray-800">{modelData.metadata.category}</span>
                          </div>
                        )}
                        {modelData.metadata.natural_language_source && (
                          <div>
                            <span className="text-sm font-medium text-gray-600">Original Query: </span>
                            <span className="text-sm text-gray-800">{modelData.metadata.natural_language_source}</span>
                          </div>
                        )}
                        {modelData.metadata.created_by && (
                          <div>
                            <span className="text-sm font-medium text-gray-600">Created By: </span>
                            <span className="text-sm text-gray-800">{modelData.metadata.created_by}</span>
                          </div>
                        )}
                        {(modelData.metadata.genie_conversation_id || modelData.metadata.genie_message_id) && (
                          <div className="pt-2 border-t">
                            <span className="text-xs text-gray-500">
                              Genie IDs: {modelData.metadata.genie_conversation_id} / {modelData.metadata.genie_message_id}
                            </span>
                          </div>
                        )}
                      </div>
                    </div>
                  )}

                  {/* Raw YAML View/Edit */}
                  <div>
                    <div className="flex items-center justify-between mb-3">
                      <h4 className="text-lg font-medium text-gray-900">Raw YAML</h4>
                      {isEditing && (
                        <div className="flex items-center space-x-2">
                          <button
                            type="button"
                            className="inline-flex items-center rounded-md bg-red-600 px-2 py-1 text-xs font-semibold text-white shadow-sm hover:bg-red-500"
                            onClick={handleCancelEdit}
                            disabled={isSaving}
                          >
                            <XCircleIcon className="h-3 w-3 mr-1" />
                            Cancel
                          </button>
                          <button
                            type="button"
                            className="inline-flex items-center rounded-md bg-green-600 px-2 py-1 text-xs font-semibold text-white shadow-sm hover:bg-green-500 disabled:opacity-50"
                            onClick={handleSaveEdit}
                            disabled={isSaving}
                          >
                            <CheckIcon className="h-3 w-3 mr-1" />
                            {isSaving ? 'Saving...' : 'Save'}
                          </button>
                        </div>
                      )}
                    </div>
                    
                    {saveError && (
                      <div className="mb-3 p-3 bg-red-50 border border-red-200 rounded-md">
                        <p className="text-sm text-red-600">{saveError}</p>
                      </div>
                    )}
                    
                    {isEditing ? (
                      <textarea
                        value={editedYaml}
                        onChange={(e) => setEditedYaml(e.target.value)}
                        className="w-full h-96 text-xs font-mono bg-gray-900 text-gray-100 p-4 rounded border-0 focus:ring-2 focus:ring-blue-500"
                        disabled={isSaving}
                      />
                    ) : (
                      <pre className="text-xs bg-gray-900 text-gray-100 p-4 rounded overflow-x-auto">
                        {model.raw_yaml || JSON.stringify(modelData, null, 2)}
                      </pre>
                    )}
                  </div>
                </div>

                <div className="mt-6 flex justify-end">
                  <button
                    type="button"
                    className="inline-flex justify-center rounded-md border border-transparent bg-gray-100 px-4 py-2 text-sm font-medium text-gray-900 hover:bg-gray-200 focus:outline-none focus-visible:ring-2 focus-visible:ring-gray-500 focus-visible:ring-offset-2"
                    onClick={onClose}
                  >
                    Close
                  </button>
                </div>
              </Dialog.Panel>
            </Transition.Child>
          </div>
        </div>
      </Dialog>
    </Transition>
  );
}

export default ModelDetailModal;
