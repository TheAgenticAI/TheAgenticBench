import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

interface Model {
  value: string;
  label: string;
  icon: React.ReactNode;
}

interface ModelSelectProps {
  models: Model[];
  value?: string;
  onValueChange?: (value: string) => void;
}

const ModelSelect: React.FC<ModelSelectProps> = ({
  models,
  value,
  onValueChange,
}) => {
  const selectedModel = (models as Model[]).find(
    (model) => model.value === value
  );

  return (
    <div className="space-y-2 w-full">
      <p className="text-muted-foreground">Model</p>
      <Select value={value} onValueChange={onValueChange}>
        <SelectTrigger className="w-full bg-secondary border focus:ring-0">
          <SelectValue>
            <div className="flex items-center gap-2">
              {selectedModel?.icon}
              <span>{selectedModel?.label}</span>
            </div>
          </SelectValue>
        </SelectTrigger>
        <SelectContent className="bg-secondary border">
          <SelectGroup>
            {models?.map((model) => (
              <SelectItem
                key={model.value}
                value={model.value}
                className={`cursor-pointer ${
                  model.value === selectedModel?.value ? "bg-gray-700" : ""
                }`}
              >
                <div className="flex items-center gap-2">
                  {model.icon}
                  <span className="text-white">{model.label}</span>
                </div>
              </SelectItem>
            ))}
          </SelectGroup>
        </SelectContent>
      </Select>
    </div>
  );
};

export default ModelSelect;
