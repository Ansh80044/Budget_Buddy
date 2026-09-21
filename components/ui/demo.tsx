import { FinancialHero } from '@/components/ui/hero-section';

// Demo component showcasing Budget Buddy FinancialHero
const FinancialHeroDemo = () => {
  return (
    <div className="w-full bg-background">
      <FinancialHero
        title={
          <>
            Smart Finance & AI Budgeting for <br />
            <span className="text-primary">College Students</span>
          </>
        }
        description="Master your money with Budget Buddy: scan receipts instantly with AI, build adaptive student budgets, simulate what-if scenarios, and unlock personalized financial guidance tailored for campus life."
        buttonText="Get Started Free"
        buttonLink="/register"
        imageUrl1="https://images.unsplash.com/photo-1559526324-4b87b5e36e44?auto=format&fit=crop&w=800&q=80"
        imageUrl2="https://images.unsplash.com/photo-1563986768609-322da13575f3?auto=format&fit=crop&w=800&q=80"
      />
    </div>
  );
};

export default FinancialHeroDemo;
