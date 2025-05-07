import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { AlertTriangle } from "lucide-react";

export function EthicalDisclosure() {
  return (
    <Card className="mt-8 border-destructive bg-destructive/10">
      <CardHeader className="flex flex-row items-center space-x-2 pb-2">
        <AlertTriangle className="h-6 w-6 text-destructive" />
        <CardTitle className="text-destructive">Important: Ethical & Legal Considerations</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3 text-sm text-destructive-foreground/90">
        <p>
          <strong>Warning:</strong> This tool is designed for legitimate research on publicly accessible data.
          Downloading, possessing, or misusing data breach information may have severe legal and ethical consequences.
        </p>
        <ul className="list-disc space-y-1 pl-5">
          <li>
            <strong>Authorized Use Only:</strong> Only use this tool if you have explicit authorization or if you are conducting research on data that is unequivocally in the public domain and legally permissible to access.
          </li>
          <li>
            <strong>Compliance with Laws:</strong> You are solely responsible for complying with all applicable local, national, and international laws regarding data privacy, data protection, and computer misuse.
          </li>
          <li>
            <strong>Respect Privacy:</strong> Exercise extreme caution and respect individual privacy. Avoid accessing or distributing personally identifiable information (PII) or sensitive data without proper authorization.
          </li>
          <li>
            <strong>Disclaimer of Liability:</strong> The creators and distributors of this tool are not liable for any misuse or illegal activity conducted with this software. Use at your own risk and discretion.
          </li>
        </ul>
        <p>
          By using BreachWatch, you acknowledge these risks and agree to use the tool responsibly and ethically.
        </p>
      </CardContent>
    </Card>
  );
}
