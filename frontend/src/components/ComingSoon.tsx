import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

export function ComingSoon({ title, phase }: { title: string; phase: string }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>{title}</CardTitle>
        <CardDescription>This screen will be implemented in {phase}.</CardDescription>
      </CardHeader>
      <CardContent className="text-sm text-muted-foreground">
        The backend endpoints for this feature are not wired up yet.
      </CardContent>
    </Card>
  );
}
