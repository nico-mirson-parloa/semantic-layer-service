import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { getModels, getModel } from '../services/api';
import ModelDetailModal from '../components/ModelDetailModal';
import { DocumentTextIcon, ChartBarIcon } from '@heroicons/react/24/outline';

function ModelsPage() {
  const [selectedModel, setSelectedModel] = useState<any>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  
  const { data: models, isLoading, refetch } = useQuery({
    queryKey: ['models'],
    queryFn: getModels,
  });

  const handleModelClick = async (modelId: string) => {
    console.log('Model clicked:', modelId);
    try {
      console.log('Fetching model details...');
      const modelDetails = await getModel(modelId);
      console.log('Model details received:', modelDetails);
      setSelectedModel(modelDetails);
      setIsModalOpen(true);
      console.log('Modal should be open now');
    } catch (error) {
      console.error('Failed to load model details:', error);
      alert(`Failed to load model details: ${error}`);
    }
  };

  const handleCloseModal = () => {
    setIsModalOpen(false);
    setSelectedModel(null);
  };

  const handleModelUpdated = () => {
    refetch(); // Refresh the models list
    // Also refresh the selected model
    if (selectedModel) {
      getModel(selectedModel.id).then(setSelectedModel);
    }
  };

  React.useEffect(() => {
    // Refresh models list when component mounts
    refetch();
  }, [refetch]);

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900">Semantic Models</h2>
        <p className="mt-2 text-gray-600">
          Manage semantic models that define metrics, dimensions, and measures
        </p>
      </div>

      {isLoading ? (
        <div className="bg-white shadow rounded-lg p-6">
          <p className="text-gray-500">Loading models...</p>
        </div>
      ) : models && models.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {models.map((model: any) => (
            <div 
              key={model.id} 
              className="bg-white shadow rounded-lg p-6 cursor-pointer hover:shadow-lg transition-shadow"
              onClick={() => handleModelClick(model.id)}
            >
              <div className="flex items-start justify-between">
                <DocumentTextIcon className="h-8 w-8 text-gray-400" />
                <ChartBarIcon className="h-5 w-5 text-blue-500" />
              </div>
              <h3 className="text-lg font-medium text-gray-900 mt-4">{model.name}</h3>
              {model.description && (
                <p className="mt-2 text-sm text-gray-600 line-clamp-2">{model.description}</p>
              )}
              <div className="mt-4 flex items-center justify-between">
                <span className="text-xs text-gray-500">ID: {model.id}</span>
                <span className="text-xs text-blue-600 hover:text-blue-800">
                  Click to view →
                </span>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="bg-white shadow rounded-lg p-6">
          <p className="text-gray-500">No semantic models found</p>
          <p className="mt-2 text-sm text-gray-400">
            Create metrics using the Natural Language Metric Builder and save them as semantic models
          </p>
        </div>
      )}

      {/* Model Detail Modal */}
      <ModelDetailModal 
        isOpen={isModalOpen}
        onClose={handleCloseModal}
        model={selectedModel}
        onModelUpdated={handleModelUpdated}
      />
    </div>
  );
}

export default ModelsPage;
