import { Navbar } from "@/components/marketing/navbar";
import { Hero } from "@/components/marketing/hero";
import { CapabilitiesSection } from "@/components/marketing/CapabilitiesSection";
import { WorkflowSection } from "@/components/marketing/WorkflowSection";
import { ArchitectureSection } from "@/components/marketing/ArchitectureSection";
import { CTASection } from "@/components/marketing/CTASection";
import { Footer } from "@/components/marketing/Footer";
import { LandingBackground } from "@/components/marketing/LandingBackground";

export default function HomePage() {
  return (
    <main className="relative min-h-screen overflow-x-hidden bg-[#090d0d]">
      <LandingBackground />
      <div className="relative z-10">
        <Navbar />
        <Hero />
        <CapabilitiesSection />
        <WorkflowSection />
        <ArchitectureSection />
        <CTASection />
        <Footer />
      </div>
    </main>
  );
}
