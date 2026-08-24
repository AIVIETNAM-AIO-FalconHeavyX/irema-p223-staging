import type { OnboardingStep } from "../types";

export interface LearningModule {
  id: number;
  title: string;
  description: string;
  steps: OnboardingStep[];
}

const MODULES = [
  {
    id: 1,
    title: "Tổng quan và hội nhập",
    description: "Tìm hiểu VinFast, văn hóa, định hướng và quy trình làm việc.",
  },
  {
    id: 2,
    title: "Kiến thức chuyên môn",
    description: "Nội dung đào tạo chuyên môn dành riêng cho vai trò của bạn.",
  },
  {
    id: 3,
    title: "Chương trình hiện tại đang triển khai còn hiệu lực",
    description: "Cập nhật chương trình, chính sách và hướng dẫn đang được áp dụng.",
  },
] as const;

export function buildLearningModules(steps: OnboardingStep[]): LearningModule[] {
  const maxOrder = steps.reduce((max, step) => Math.max(max, step.order), 0);
  
  const module1Steps = steps.filter(step => step.order <= 1);
  const module3Steps = steps.filter(step => maxOrder > 1 && step.order >= maxOrder);
  const module2Steps = steps.filter(step => step.order > 1 && step.order < maxOrder);

  return MODULES.map((module, index) => {
    if (index === 0) return { ...module, steps: module1Steps };
    if (index === 1) return { ...module, steps: module2Steps };
    return { ...module, steps: module3Steps };
  });
}

export function moduleResourceCount(module: LearningModule): number {
  return module.steps.reduce((total, step) => total + step.resources.length, 0);
}

export function moduleDuration(module: LearningModule): number {
  return module.steps.reduce((total, step) => total + step.duration_minutes, 0);
}
