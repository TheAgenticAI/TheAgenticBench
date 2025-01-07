import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import {BrainElectricity} from "iconoir-react";

interface AccordionItemProps {
  title: string;
  content: string;
}

export const AccordionGroup = ({items}: {items: AccordionItemProps[]}) => {
  return (
    <Accordion type="single" collapsible className="w-full space-y-3">
      {items.map((item, idx) => (
        <AccordionItem key={idx} value={`item-${idx}`}>
          <AccordionTrigger>
            <div className="flex flex-row items-center gap-2">
              <BrainElectricity />
              {item.title}
            </div>
          </AccordionTrigger>
          <AccordionContent>{item.content}</AccordionContent>
        </AccordionItem>
      ))}
    </Accordion>
  );
};
