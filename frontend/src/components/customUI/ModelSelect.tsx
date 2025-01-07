import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {useState} from "react";

export interface ModelProps {
  name: string;
  icon: React.ReactElement;
  type: string;
}

export const ModelSelect = ({models}: {models: ModelProps[]}) => {
  const [selectedModel, setSelectedModel] = useState<string>(models[0].name);

  return (
    <Select value={selectedModel} onValueChange={setSelectedModel}>
      <SelectTrigger className="w-full">
        <SelectValue placeholder="Select a Model" />
      </SelectTrigger>
      <SelectContent>
        {models.map((model) => (
          <SelectItem value={model.name}>{model.name}</SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
};
