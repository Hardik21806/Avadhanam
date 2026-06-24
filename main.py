import argparse
import sys
from src.experiment import run_experiment
from src.evaluate_offline import evaluate_model


def main():
    parser = argparse.ArgumentParser(
        description="Avadhanam Experiment & Evaluation Suite",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run experiment with 3 questioners without distractors (default model: Groq Llama 3.3)
  python main.py experiment --model-path data/output/Groq_Llama3.3 --questioners 3
  
  # Run experiment with distractors
  python main.py experiment --model-path data/output/Groq_Llama3.3 --questioners 3 --distractors
  
  # Run experiment with custom model
  python main.py experiment --model-path data/output/OpenAI_GPT4 --questioners 3 --distractors \\
    --base-url https://api.openai.com/v1 --model-name gpt-4 --api-key-env OPENAI_API_KEY
  
  # Run evaluation (creates separate results for with/without distractors)
  python main.py evaluate --model-path data/output/Groq_Llama3.3

Directory Structure:
  data/output/<model_name>/
    with_distractor/
      3_questioners_1.json
      3_questioners_2.json
      4_questioners_1.json
    without_distractor/
      3_questioners_1.json
      3_questioners_2.json
      4_questioners_1.json
  
  Evaluation Output:
    evaluation_results_with_distractor.csv
    evaluation_results_without_distractor.csv
    evaluation_plots_with_distractor.png
    evaluation_plots_without_distractor.png
  
  Each JSON file contains all poem pairs from one avadhana session
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # ==================== EXPERIMENT COMMAND ====================
    exp_parser = subparsers.add_parser('experiment', help='Run an experiment')
    exp_parser.add_argument(
        '--model-path',
        type=str,
        default='data/output/Groq_Llama3.3',
        help='Base path for model output (e.g., data/output/Groq_Llama3.3). Results will be saved to with_distractor/ or without_distractor/ subfolder'
    )
    exp_parser.add_argument(
        '--questioners',
        type=int,
        required=True,
        help='Number of questioners (e.g., 3, 4, 5)'
    )
    exp_parser.add_argument(
        '--distractors',
        action='store_true',
        default=False,
        help='Include distractor rounds in the experiment'
    )
    exp_parser.add_argument(
        '--count',
        type=int,
        default=1,
        help='Number of experiments to run for this configuration (default: 1)'
    )
    exp_parser.add_argument(
        '--base-url',
        type=str,
        default=None,
        help='API base URL (default: https://api.groq.com/openai/v1)'
    )
    exp_parser.add_argument(
        '--model-name',
        type=str,
        default=None,
        help='Model name (default: llama-3.3-70b-versatile)'
    )
    exp_parser.add_argument(
        '--api-key-env',
        type=str,
        default=None,
        help='Environment variable for API key (default: GROQ_API_KEY)'
    )
    
    # ==================== EVALUATE COMMAND ====================
    eval_parser = subparsers.add_parser('evaluate', help='Run evaluation on experimental results')
    eval_parser.add_argument(
        '--model-path',
        type=str,
        required=True,
        help='Path to model output directory (e.g., data/output/Groq_Llama3.3)'
    )
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # ==================== HANDLE EXPERIMENT ====================
    if args.command == 'experiment':
        print(f"\nRunning {args.count} experiment(s) with {args.questioners} questioners")
        print(f"Model path: {args.model_path}")
        print(f"Distractors: {args.distractors}")
        if args.base_url:
            print(f"Base URL: {args.base_url}")
        if args.model_name:
            print(f"Model: {args.model_name}")
        print()
        
        for i in range(args.count):
            print(f"\n[Experiment {i+1}/{args.count}]")
            try:
                mrs, wos, tms, adherence = run_experiment(
                    model_base_path=args.model_path,
                    questioner_count=args.questioners,
                    use_distractors=args.distractors,
                    base_url=args.base_url,
                    model_name=args.model_name,
                    api_key_env=args.api_key_env
                )
                print(f"✓ Experiment {i+1} completed successfully")
            except Exception as e:
                print(f"✗ Experiment {i+1} failed: {e}")
                import traceback
                traceback.print_exc()
                continue
        
        print(f"\n{'='*60}")
        print("All experiments completed!")
        distractor_folder = "with_distractor" if args.distractors else "without_distractor"
        print(f"Results saved to: {args.model_path}/{distractor_folder}/")
        print(f"File naming: <questioners>_questioners_<iteration>.json")
        print(f"Example: {args.questioners}_questioners_1.json, {args.questioners}_questioners_2.json, ...")
        print(f"{'='*60}\n")
    
    # ==================== HANDLE EVALUATE ====================
    elif args.command == 'evaluate':
        print(f"\nRunning evaluation...")
        print(f"Model path: {args.model_path}\n")
        
        try:
            df = evaluate_model(args.model_path)
            print(f"\n{'='*60}")
            print("Evaluation completed successfully!")
            print(f"CSV saved to: {args.model_path}/evaluation_results.csv")
            print(f"Plots saved to: {args.model_path}/evaluation_plots.png")
            print(f"{'='*60}\n")
        except Exception as e:
            print(f"Evaluation failed: {e}")
            sys.exit(1)


if __name__ == "__main__":
    main()
