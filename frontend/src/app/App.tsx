import { useMemo, useState } from "react";

import { AppLayout } from "../components/AppLayout";
import { DashboardView } from "../features/dashboard/DashboardView";
import { DocumentsView } from "../features/documents/DocumentsView";
import { ProcessesView } from "../features/processes/ProcessesView";
import { ProjectsView } from "../features/projects/ProjectsView";
import { TemplatesView } from "../features/templates/TemplatesView";
import { TasksView } from "../features/tasks/TasksView";

export type AppSection = "dashboard" | "projects" | "tasks" | "processes" | "documents" | "templates";

export function App() {
  const [activeSection, setActiveSection] = useState<AppSection>("dashboard");

  const content = useMemo(() => {
    if (activeSection === "dashboard") {
      return <DashboardView />;
    }
    if (activeSection === "tasks") {
      return <TasksView />;
    }
    if (activeSection === "processes") {
      return <ProcessesView />;
    }
    if (activeSection === "documents") {
      return <DocumentsView />;
    }
    if (activeSection === "templates") {
      return <TemplatesView />;
    }
    return <ProjectsView />;
  }, [activeSection]);

  return (
    <AppLayout activeSection={activeSection} onNavigate={setActiveSection}>
      {content}
    </AppLayout>
  );
}
