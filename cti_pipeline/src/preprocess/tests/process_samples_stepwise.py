"""
CTI Pipeline Step-by-Step Processing and Output Saver

This script processes all sample files through each step of the CTI preprocessing pipeline
and saves the output from each step to organized directories for analysis and testing.

Output Structure:
- test/extraction_output/: Raw extracted text from files
- test/cleaning_output/: Text after cleaning step
- test/normalization_output/: Text after normalization step  
- test/chunking_output/: Text after chunking step
- test/metadata/: Processing metadata and statistics for each file

Note: Anonymization step is currently disabled and commented out.
"""

import os
import sys
import json
import time
from pathlib import Path
from typing import Dict, List, Any, Optional

# Add the core module to the path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
core_dir = os.path.join(parent_dir, 'core')
sys.path.insert(0, core_dir)

from processors.extraction.extraction import TextExtractor, ExtractionResult
from processors.cleaning.cleaning import TextCleaner
from processors.cleaning.normalization import TextNormalizer
# from processors.anonymization.anonymizer import TextAnonymizer
# from processors.anonymization.config import AnonymizationConfig
from processors.chunking.chunker import CTIChunker
from processors.chunking.config import ChunkingConfig


class StepByStepProcessor:
    """Process files step by step and save outputs"""
    
    def __init__(self):
        self.base_dir = "test"
        self.extraction_dir = os.path.join(self.base_dir, "extraction_output")
        self.cleaning_dir = os.path.join(self.base_dir, "cleaning_output")
        self.normalization_dir = os.path.join(self.base_dir, "normalization_output")
        # self.anonymization_dir = os.path.join(self.base_dir, "anonymization_output")
        self.chunking_dir = os.path.join(self.base_dir, "chunking_output")
        self.metadata_dir = os.path.join(self.base_dir, "metadata")
        
        # Create output directories if they don't exist
        self.create_output_directories()
        
        # Initialize processors
        self.extractor = TextExtractor()
        self.cleaner = TextCleaner()
        self.normalizer = TextNormalizer()
        # self.anonymizer = TextAnonymizer(AnonymizationConfig(
        #     anonymize_emails=True,
        #     anonymize_phones=True,
        #     anonymize_names=True,
        #     preserve_technical_terms=True,
        #     preserve_iocs=True
        # ))
        self.chunker = CTIChunker(ChunkingConfig(
            chunk_strategy="ioc_based",
            window_size=2,
            fallback_to_regex=True,
            use_llm_extraction=True
        ))
        
        # Statistics
        self.processing_stats = {}
    
    def create_output_directories(self):
        """Create all output directories if they don't exist"""
        directories = [
            self.base_dir,
            self.extraction_dir,
            self.cleaning_dir,
            self.normalization_dir,
            # self.anonymization_dir,
            self.chunking_dir,
            self.metadata_dir
        ]
        
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
            print(f"📁 Created directory: {directory}")
    
    
    def get_safe_filename(self, file_path: str, step: str) -> str:
        """Generate a safe filename for output"""
        original_name = Path(file_path).stem
        extension = Path(file_path).suffix
        
        # Replace problematic characters
        safe_name = original_name.replace(" ", "_").replace("-", "_")
        safe_name = "".join(c for c in safe_name if c.isalnum() or c in "_.")
        
        return f"{safe_name}_{step}.txt"
    
    def save_text_output(self, text: str, file_path: str, step: str, output_dir: str):
        """Save text output to specified directory"""
        filename = self.get_safe_filename(file_path, step)
        output_path = os.path.join(output_dir, filename)
        
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(text)
            print(f"    ✅ Saved {step}: {filename} ({len(text):,} chars)")
            return True
        except Exception as e:
            print(f"    ❌ Failed to save {step}: {e}")
            return False
    
    def save_metadata(self, file_path: str, metadata: Dict[str, Any]):
        """Save processing metadata"""
        filename = self.get_safe_filename(file_path, "metadata")
        filename = filename.replace("_metadata.txt", "_metadata.json")
        output_path = os.path.join(self.metadata_dir, filename)
        
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, default=str)
            print(f"    📊 Saved metadata: {filename}")
            return True
        except Exception as e:
            print(f"    ❌ Failed to save metadata: {e}")
            return False
    
    def save_chunking_output(self, chunking_result, file_path: str):
        """Save chunking output as JSON"""
        filename = self.get_safe_filename(file_path, "chunked")
        filename = filename.replace("_chunked.txt", "_chunked.json")
        output_path = os.path.join(self.chunking_dir, filename)
        
        try:
            output_data = {
                "metadata": chunking_result.get_summary(),
                "chunks": chunking_result.chunks,
                "processing_details": {
                    "strategy_used": chunking_result.strategy_used,
                    "window_size": chunking_result.window_size,
                    "extraction_time": chunking_result.extraction_time,
                    "chunking_time": chunking_result.chunking_time,
                    "total_processing_time": chunking_result.processing_time,
                    "success": chunking_result.success,
                    "errors": chunking_result.errors
                }
            }
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, indent=2, default=str)
            
            print(f"    ✅ Saved chunking: {filename} ({chunking_result.total_chunks} chunks)")
            return True
        except Exception as e:
            print(f"    ❌ Failed to save chunking: {e}")
            return False
    
    def process_file_step_by_step(self, file_path: str) -> Dict[str, Any]:
        """Process a single file through all steps and save outputs"""
        file_name = os.path.basename(file_path)
        print(f"\\n📄 Processing: {file_name}")
        print("-" * 50)
        
        metadata = {
            "original_file": file_path,
            "file_name": file_name,
            "file_size": os.path.getsize(file_path),
            "processing_timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "steps": {},
            "summary": {}
        }
        
        current_text = ""
        step_success = {}
        
        # Step 1: Extraction
        print("  🔧 Step 1: Text Extraction")
        start_time = time.time()
        
        try:
            extraction_result = self.extractor.extract_from_file(file_path)
            extraction_time = time.time() - start_time
            
            if extraction_result.success:
                current_text = extraction_result.text
                saved = self.save_text_output(current_text, file_path, "extracted", self.extraction_dir)
                step_success["extraction"] = saved
                
                metadata["steps"]["extraction"] = {
                    "success": True,
                    "processing_time": extraction_time,
                    "output_length": len(current_text),
                    "file_format": extraction_result.file_format,
                    "metadata": extraction_result.metadata
                }
                print(f"    ⏱️ Time: {extraction_time:.3f}s")
            else:
                print(f"    ❌ Extraction failed: {extraction_result.error_message}")
                metadata["steps"]["extraction"] = {
                    "success": False,
                    "error": extraction_result.error_message,
                    "processing_time": extraction_time
                }
                return metadata
        
        except Exception as e:
            print(f"    💥 Extraction error: {e}")
            metadata["steps"]["extraction"] = {
                "success": False,
                "error": str(e),
                "processing_time": time.time() - start_time
            }
            return metadata
        
        # Step 2: Cleaning
        print("  🧹 Step 2: Text Cleaning")
        start_time = time.time()
        
        try:
            original_length = len(current_text)
            cleaned_text = self.cleaner.clean(current_text)
            cleaning_time = time.time() - start_time
            
            saved = self.save_text_output(cleaned_text, file_path, "cleaned", self.cleaning_dir)
            step_success["cleaning"] = saved
            
            reduction = ((original_length - len(cleaned_text)) / original_length * 100) if original_length > 0 else 0
            
            metadata["steps"]["cleaning"] = {
                "success": True,
                "processing_time": cleaning_time,
                "input_length": original_length,
                "output_length": len(cleaned_text),
                "reduction_percentage": round(reduction, 2)
            }
            
            current_text = cleaned_text
            print(f"    ⏱️ Time: {cleaning_time:.3f}s")
            print(f"    📉 Reduction: {reduction:.1f}%")
        
        except Exception as e:
            print(f"    💥 Cleaning error: {e}")
            metadata["steps"]["cleaning"] = {
                "success": False,
                "error": str(e),
                "processing_time": time.time() - start_time
            }
            step_success["cleaning"] = False
        
        # Step 3: Normalization
        print("  📐 Step 3: Text Normalization")
        start_time = time.time()
        
        try:
            original_length = len(current_text)
            normalized_text = self.normalizer.normalize(current_text)
            normalization_time = time.time() - start_time
            
            saved = self.save_text_output(normalized_text, file_path, "normalized", self.normalization_dir)
            step_success["normalization"] = saved
            
            metadata["steps"]["normalization"] = {
                "success": True,
                "processing_time": normalization_time,
                "input_length": original_length,
                "output_length": len(normalized_text)
            }
            
            current_text = normalized_text
            print(f"    ⏱️ Time: {normalization_time:.3f}s")
        
        except Exception as e:
            print(f"    💥 Normalization error: {e}")
            metadata["steps"]["normalization"] = {
                "success": False,
                "error": str(e),
                "processing_time": time.time() - start_time
            }
            step_success["normalization"] = False
        
        # Step 4: Anonymization (commented out)
        # print("  🔒 Step 4: Text Anonymization")
        # start_time = time.time()
        # 
        # try:
        #     original_length = len(current_text)
        #     anonymized_text = self.anonymizer.anonymize(current_text)
        #     anonymization_time = time.time() - start_time
        #     
        #     saved = self.save_text_output(anonymized_text, file_path, "anonymized", self.anonymization_dir)
        #     step_success["anonymization"] = saved
        #     
        #     metadata["steps"]["anonymization"] = {
        #         "success": True,
        #         "processing_time": anonymization_time,
        #         "input_length": original_length,
        #         "output_length": len(anonymized_text)
        #     }
        #     
        #     current_text = anonymized_text
        #     print(f"    ⏱️ Time: {anonymization_time:.3f}s")
        # 
        # except Exception as e:
        #     print(f"    💥 Anonymization error: {e}")
        #     metadata["steps"]["anonymization"] = {
        #         "success": False,
        #         "error": str(e),
        #         "processing_time": time.time() - start_time
        #     }
        #     step_success["anonymization"] = False
        
        # Step 5: Chunking (now Step 4)
        print("  🔗 Step 4: Text Chunking")
        start_time = time.time()
        
        try:
            chunking_result = self.chunker.chunk(current_text)
            chunking_time = time.time() - start_time
            
            saved = self.save_chunking_output(chunking_result, file_path)
            step_success["chunking"] = saved
            
            metadata["steps"]["chunking"] = {
                "success": chunking_result.success,
                "processing_time": chunking_time,
                "input_length": len(current_text),
                "total_chunks": chunking_result.total_chunks,
                "iocs_found": chunking_result.iocs_found,
                "strategy_used": chunking_result.strategy_used,
                "window_size": chunking_result.window_size,
                "extraction_time": chunking_result.extraction_time,
                "chunking_time": chunking_result.chunking_time,
                "errors": chunking_result.errors
            }
            
            print(f"    ⏱️ Time: {chunking_time:.3f}s")
            print(f"    📊 Chunks: {chunking_result.total_chunks}")
            print(f"    🎯 IOCs: {chunking_result.iocs_found}")
            print(f"    📝 Strategy: {chunking_result.strategy_used}")
        
        except Exception as e:
            print(f"    💥 Chunking error: {e}")
            metadata["steps"]["chunking"] = {
                "success": False,
                "error": str(e),
                "processing_time": time.time() - start_time
            }
            step_success["chunking"] = False
        
        # Calculate summary
        total_time = sum(
            step_data.get("processing_time", 0) 
            for step_data in metadata["steps"].values()
        )
        
        successful_steps = sum(1 for success in step_success.values() if success)
        
        metadata["summary"] = {
            "total_processing_time": total_time,
            "successful_steps": successful_steps,
            "total_steps": len(step_success),
            "success_rate": (successful_steps / len(step_success) * 100) if step_success else 0,
            "final_text_length": len(current_text)
        }
        
        # Save metadata
        self.save_metadata(file_path, metadata)
        
        print(f"  ✅ Completed: {successful_steps}/{len(step_success)} steps successful")
        print(f"  ⏱️ Total time: {total_time:.3f}s")
        
        return metadata
    
    def discover_sample_files(self) -> List[str]:
        """Discover all sample files to process"""
        files = []
        
        # Check samples directory
        samples_dir = "../../../samples"
        if os.path.exists(samples_dir):
            for file in os.listdir(samples_dir):
                file_path = os.path.join(samples_dir, file)
                if os.path.isfile(file_path):
                    files.append(file_path)
        
        # Check PDFs directory
        pdfs_dir = "../../../PDFs"
        if os.path.exists(pdfs_dir):
            for file in os.listdir(pdfs_dir):
                if file.lower().endswith('.pdf'):
                    files.append(os.path.join(pdfs_dir, file))
        
        return files
    
    def process_all_samples(self):
        """Process all sample files and save step outputs"""
        print("🔄 CTI PIPELINE - STEP-BY-STEP PROCESSING")
        print("=" * 60)
        
        # Discover files
        sample_files = self.discover_sample_files()
        
        if not sample_files:
            print("❌ No sample files found!")
            print("Expected locations:")
            print("  - ../../samples/")
            print("  - ../../PDFs/")
            return
        
        print(f"📁 Found {len(sample_files)} files to process:")
        for file_path in sample_files:
            file_name = os.path.basename(file_path)
            file_size = os.path.getsize(file_path)
            print(f"  • {file_name} ({file_size:,} bytes)")
        
        print(f"\\n💾 Output directories:")
        print(f"  • Extraction: {self.extraction_dir}")
        print(f"  • Cleaning: {self.cleaning_dir}")
        print(f"  • Normalization: {self.normalization_dir}")
        # print(f"  • Anonymization: {self.anonymization_dir}")
        print(f"  • Chunking: {self.chunking_dir}")
        print(f"  • Metadata: {self.metadata_dir}")
        
        # Process each file
        all_metadata = {}
        successful_files = 0
        total_processing_time = 0
        
        for i, file_path in enumerate(sample_files, 1):
            print(f"\\n{'='*60}")
            print(f"📊 PROCESSING FILE {i}/{len(sample_files)}")
            print(f"{'='*60}")
            
            try:
                file_metadata = self.process_file_step_by_step(file_path)
                all_metadata[file_path] = file_metadata
                
                if file_metadata["summary"]["successful_steps"] > 0:
                    successful_files += 1
                
                total_processing_time += file_metadata["summary"]["total_processing_time"]
            
            except Exception as e:
                print(f"💥 Failed to process {file_path}: {e}")
                all_metadata[file_path] = {
                    "error": str(e),
                    "success": False
                }
        
        # Save overall summary
        self.save_processing_summary(all_metadata, successful_files, total_processing_time)
        
        # Final report
        print(f"\\n{'='*60}")
        print("📋 PROCESSING COMPLETE")
        print(f"{'='*60}")
        print(f"✅ Files successfully processed: {successful_files}/{len(sample_files)}")
        print(f"⏱️ Total processing time: {total_processing_time:.3f}s")
        print(f"🚀 Average time per file: {total_processing_time/len(sample_files):.3f}s")
        
        print(f"\\n📂 Check the following directories for outputs:")
        print(f"  • {self.extraction_dir}/")
        print(f"  • {self.cleaning_dir}/")
        print(f"  • {self.normalization_dir}/")
        # print(f"  • {self.anonymization_dir}/")
        print(f"  • {self.chunking_dir}/")
        print(f"  • {self.metadata_dir}/")
    
    def save_processing_summary(self, all_metadata: Dict, successful_files: int, total_time: float):
        """Save overall processing summary"""
        summary = {
            "processing_session": {
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "total_files": len(all_metadata),
                "successful_files": successful_files,
                "total_processing_time": total_time,
                "average_time_per_file": total_time / len(all_metadata) if all_metadata else 0
            },
            "files": all_metadata,
            "statistics": {
                "extraction_success": sum(1 for meta in all_metadata.values() 
                                        if meta.get("steps", {}).get("extraction", {}).get("success", False)),
                "cleaning_success": sum(1 for meta in all_metadata.values() 
                                      if meta.get("steps", {}).get("cleaning", {}).get("success", False)),
                "normalization_success": sum(1 for meta in all_metadata.values() 
                                           if meta.get("steps", {}).get("normalization", {}).get("success", False)),
                # "anonymization_success": sum(1 for meta in all_metadata.values() 
                #                            if meta.get("steps", {}).get("anonymization", {}).get("success", False)),
                "chunking_success": sum(1 for meta in all_metadata.values() 
                                      if meta.get("steps", {}).get("chunking", {}).get("success", False))
            }
        }
        
        summary_path = os.path.join(self.metadata_dir, "processing_summary.json")
        
        try:
            with open(summary_path, 'w', encoding='utf-8') as f:
                json.dump(summary, f, indent=2, default=str)
            print(f"\\n📊 Processing summary saved: {summary_path}")
        except Exception as e:
            print(f"\\n❌ Failed to save processing summary: {e}")


def main():
    """Run the step-by-step processor"""
    # Change to the script directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    try:
        processor = StepByStepProcessor()
        processor.process_all_samples()
        
        print(f"\\n🎉 All done! Check the 'test/' directory for outputs.")
        
    except Exception as e:
        print(f"💥 Processing failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
