"""Property-based tests for CLI Adapter component.

**Validates: Requirements 8.3, 8.4**
"""

import io
import sys
from hypothesis import given, strategies as st, settings

from adapters.cli_adapter import CLIAdapter
from core.models import QueryResult, Answer, RetrievedChunk, Chunk, ChunkMetadata


class TestCLIAdapterProperties:
    """Property-based tests for CLIAdapter."""

    @given(
        answer_text=st.text(min_size=10, max_size=500).filter(lambda t: len(t.strip()) > 0),
        num_chunks=st.integers(min_value=1, max_value=5),
        confidence=st.sampled_from(["high", "medium", "low"]),
        processing_time=st.floats(min_value=0.1, max_value=10.0),
    )
    @settings(max_examples=100, deadline=10000)
    def test_property_15_cli_display_completeness(
        self, answer_text, num_chunks, confidence, processing_time
    ):
        """
        Property 15: CLI Display Completeness

        **Validates: Requirements 8.3, 8.4**

        For any successful query result with answer and supporting chunks,
        the CLI display should include both the answer text and supporting
        chunk information.

        Requirements:
        - 8.3: WHEN a question is submitted, THE CLI_Interface SHALL display
               the generated answer
        - 8.4: WHEN an answer is generated, THE CLI_Interface SHALL display
               the supporting context chunks
        """
        from unittest.mock import Mock

        # Create mock RAG orchestrator
        mock_orchestrator = Mock()

        # Create CLI adapter
        cli_adapter = CLIAdapter(mock_orchestrator)

        # Generate sample supporting chunks with varying content
        supporting_chunks = []
        for i in range(num_chunks):
            chunk_text = (
                f"Supporting chunk {i}: This contains relevant information about the topic. " * 2
            )
            chunk = Chunk(
                text=chunk_text,
                metadata=ChunkMetadata(
                    chunk_index=i,
                    source_document=f"test_document_{i % 3}.pd",
                    start_position=i * 200,
                    end_position=i * 200 + len(chunk_text),
                ),
            )
            retrieved_chunk = RetrievedChunk(
                chunk=chunk, similarity_score=0.95 - (i * 0.1)  # Decreasing similarity
            )
            supporting_chunks.append(retrieved_chunk)

        # Create Answer object
        answer = Answer(
            text=answer_text, supporting_chunks=supporting_chunks, confidence=confidence
        )

        # Create QueryResult
        query_result = QueryResult(answer=answer, processing_time_seconds=processing_time)

        # Capture stdout to verify display output
        captured_output = io.StringIO()
        original_stdout = sys.stdout

        try:
            sys.stdout = captured_output

            # Display the query result (Requirements 8.3, 8.4)
            cli_adapter._display_query_result(query_result, show_scores=False)

            # Get the captured output
            output = captured_output.getvalue()

        finally:
            # Restore stdout
            sys.stdout = original_stdout

        # Property assertions

        # 1. Output should not be empty
        assert len(output) > 0, "CLI display output should not be empty"

        # 2. Output should contain the answer text (Requirement 8.3)
        assert answer_text in output, "CLI display should include the answer text"

        # 3. Output should contain confidence level display
        confidence_indicators = {"high": "High", "medium": "Medium", "low": "Low"}
        expected_confidence_display = confidence_indicators[confidence]
        assert (
            expected_confidence_display in output
        ), f"CLI display should show confidence level: {expected_confidence_display}"

        # 4. Output should contain processing time
        assert (
            "Processing Time:" in output or "processing time" in output.lower()
        ), "CLI display should show processing time"
        assert (
            f"{processing_time:.2f}" in output
        ), f"CLI display should show processing time value: {processing_time:.2f}"

        # 5. Output should contain supporting chunks section (Requirement 8.4)
        assert (
            "SUPPORTING CONTEXT" in output or "supporting context" in output.lower()
        ), "CLI display should have a supporting context section"

        # 6. Output should indicate the number of chunks
        assert (
            f"{num_chunks} chunk" in output.lower()
        ), f"CLI display should indicate {num_chunks} supporting chunks"

        # 7. Output should contain text from each supporting chunk (Requirement 8.4)
        for i, retrieved_chunk in enumerate(supporting_chunks):
            # Check that chunk text appears in output
            # The display may wrap or format the text, so check for a substring
            chunk_text_sample = retrieved_chunk.chunk.text[:50]  # First 50 chars
            assert chunk_text_sample in output, f"CLI display should include text from chunk {i}"

        # 8. Output should contain metadata for each chunk (Requirement 8.4)
        for i, retrieved_chunk in enumerate(supporting_chunks):
            # Check for source document
            assert (
                retrieved_chunk.chunk.metadata.source_document in output
            ), f"CLI display should show source document for chunk {i}"

            # Check for position information
            assert (
                str(retrieved_chunk.chunk.metadata.start_position) in output
            ), f"CLI display should show start position for chunk {i}"
            assert (
                str(retrieved_chunk.chunk.metadata.end_position) in output
            ), f"CLI display should show end position for chunk {i}"

        # 9. Output should have proper formatting structure
        assert "=" in output, "CLI display should have section separators"

        # 10. Output should contain "ANSWER" section header
        assert "ANSWER" in output, "CLI display should have an ANSWER section header"

        # 11. Chunks should be numbered in the display
        for i in range(1, num_chunks + 1):
            assert (
                f"[Chunk {i}]" in output or f"Chunk {i}" in output
            ), f"CLI display should show chunk number {i}"

        # 12. Output should contain "Source:" labels for chunks
        assert (
            output.count("Source:") >= num_chunks
        ), f"CLI display should show 'Source:' label for each of {num_chunks} chunks"

        # 13. Output should contain "Position:" labels for chunks
        assert (
            output.count("Position:") >= num_chunks
        ), f"CLI display should show 'Position:' label for each of {num_chunks} chunks"

    @given(
        answer_text=st.text(min_size=10, max_size=500).filter(lambda t: len(t.strip()) > 0),
        num_chunks=st.integers(min_value=1, max_value=5),
        processing_time=st.floats(min_value=0.1, max_value=10.0),
    )
    @settings(max_examples=100, deadline=10000)
    def test_property_15_cli_display_with_scores(self, answer_text, num_chunks, processing_time):
        """
        Property 15 (Score display variant): CLI Display Completeness

        **Validates: Requirements 8.3, 8.4**

        When show_scores=True, the CLI display should include similarity
        scores for each supporting chunk in addition to answer and chunk info.

        Requirements:
        - 8.3: WHEN a question is submitted, THE CLI_Interface SHALL display
               the generated answer
        - 8.4: WHEN an answer is generated, THE CLI_Interface SHALL display
               the supporting context chunks
        """
        from unittest.mock import Mock

        # Create mock RAG orchestrator
        mock_orchestrator = Mock()

        # Create CLI adapter
        cli_adapter = CLIAdapter(mock_orchestrator)

        # Generate sample supporting chunks with specific similarity scores
        supporting_chunks = []
        similarity_scores = []
        for i in range(num_chunks):
            chunk_text = f"Chunk {i} content with information. " * 3
            similarity_score = 0.95 - (i * 0.1)
            similarity_scores.append(similarity_score)

            chunk = Chunk(
                text=chunk_text,
                metadata=ChunkMetadata(
                    chunk_index=i,
                    source_document=f"doc_{i}.pd",
                    start_position=i * 100,
                    end_position=i * 100 + len(chunk_text),
                ),
            )
            retrieved_chunk = RetrievedChunk(chunk=chunk, similarity_score=similarity_score)
            supporting_chunks.append(retrieved_chunk)

        # Create Answer and QueryResult
        answer = Answer(text=answer_text, supporting_chunks=supporting_chunks, confidence="high")

        query_result = QueryResult(answer=answer, processing_time_seconds=processing_time)

        # Capture stdout
        captured_output = io.StringIO()
        original_stdout = sys.stdout

        try:
            sys.stdout = captured_output

            # Display with show_scores=True
            cli_adapter._display_query_result(query_result, show_scores=True)

            output = captured_output.getvalue()

        finally:
            sys.stdout = original_stdout

        # Property assertions

        # 1. Output should contain answer text (Requirement 8.3)
        assert answer_text in output, "CLI display should include the answer text"

        # 2. Output should contain supporting chunks (Requirement 8.4)
        assert (
            "SUPPORTING CONTEXT" in output or "supporting context" in output.lower()
        ), "CLI display should have a supporting context section"

        # 3. Output should contain similarity scores for each chunk
        assert (
            "Similarity Score:" in output or "similarity score" in output.lower()
        ), "CLI display should show similarity scores when show_scores=True"

        # 4. Each similarity score should appear in the output
        for i, score in enumerate(similarity_scores):
            # Format score as it appears in display (4 decimal places)
            score_str = f"{score:.4f}"
            assert (
                score_str in output
            ), f"CLI display should show similarity score {score_str} for chunk {i}"

        # 5. Number of "Similarity Score:" occurrences should match number of chunks
        score_count = output.count("Similarity Score:")
        assert (
            score_count == num_chunks
        ), f"CLI display should show similarity score for each of {num_chunks} chunks, found {score_count}"

        # 6. Output should still contain all chunk metadata
        for retrieved_chunk in supporting_chunks:
            assert (
                retrieved_chunk.chunk.metadata.source_document in output
            ), "CLI display should show source document"
            assert (
                str(retrieved_chunk.chunk.metadata.start_position) in output
            ), "CLI display should show start position"

    @given(
        prefix_text=st.text(min_size=0, max_size=100),
        processing_time=st.floats(min_value=0.1, max_value=5.0),
    )
    @settings(max_examples=100, deadline=10000)
    def test_property_15_cli_display_not_found(self, prefix_text, processing_time):
        """
        Property 15 (Not found variant): CLI Display Completeness

        **Validates: Requirements 8.3, 8.4**

        When the answer is "not found", the CLI should display the answer
        text but may have empty supporting chunks section.

        Requirements:
        - 8.3: WHEN a question is submitted, THE CLI_Interface SHALL display
               the generated answer
        - 8.4: WHEN an answer is generated, THE CLI_Interface SHALL display
               the supporting context chunks
        """
        from unittest.mock import Mock

        # Construct a "not found" answer text
        answer_text = f"{prefix_text} I could not find the answer in the document.".strip()

        # Create mock RAG orchestrator
        mock_orchestrator = Mock()

        # Create CLI adapter
        cli_adapter = CLIAdapter(mock_orchestrator)

        # Create Answer with "not found" response and empty chunks
        answer = Answer(text=answer_text, supporting_chunks=[], confidence="not_found")

        query_result = QueryResult(answer=answer, processing_time_seconds=processing_time)

        # Capture stdout
        captured_output = io.StringIO()
        original_stdout = sys.stdout

        try:
            sys.stdout = captured_output

            # Display the query result
            cli_adapter._display_query_result(query_result, show_scores=False)

            output = captured_output.getvalue()

        finally:
            sys.stdout = original_stdout

        # Property assertions

        # 1. Output should contain the "not found" answer text (Requirement 8.3)
        assert answer_text in output, "CLI display should include the 'not found' answer text"

        # 2. Output should contain confidence level
        assert (
            "Not Found" in output or "not found" in output.lower()
        ), "CLI display should show 'not found' confidence level"

        # 3. Output should contain processing time
        assert "Processing Time:" in output, "CLI display should show processing time"

        # 4. Output should have ANSWER section
        assert "ANSWER" in output, "CLI display should have an ANSWER section"

        # 5. Supporting chunks section should either be absent or indicate 0 chunks
        # (since there are no supporting chunks for "not found" responses)
        if "SUPPORTING CONTEXT" in output:
            # If section exists, it should indicate 0 chunks
            assert "0 chunk" in output.lower() or not any(
                f"[Chunk {i}]" in output for i in range(1, 10)
            ), "CLI display should not show chunk details when there are no supporting chunks"

    @given(
        answer_text=st.text(min_size=10, max_size=500).filter(lambda t: len(t.strip()) > 0),
        num_chunks=st.integers(min_value=1, max_value=3),
    )
    @settings(max_examples=100, deadline=10000)
    def test_property_15_cli_display_consistency(self, answer_text, num_chunks):
        """
        Property 15 (Consistency variant): CLI Display Completeness

        **Validates: Requirements 8.3, 8.4**

        For any query result, the CLI display should consistently include
        all required elements in the same order and format.

        Requirements:
        - 8.3: WHEN a question is submitted, THE CLI_Interface SHALL display
               the generated answer
        - 8.4: WHEN an answer is generated, THE CLI_Interface SHALL display
               the supporting context chunks
        """
        from unittest.mock import Mock

        # Create mock RAG orchestrator
        mock_orchestrator = Mock()

        # Create CLI adapter
        cli_adapter = CLIAdapter(mock_orchestrator)

        # Generate supporting chunks
        supporting_chunks = []
        for i in range(num_chunks):
            chunk = Chunk(
                text=f"Chunk {i} text content. " * 5,
                metadata=ChunkMetadata(
                    chunk_index=i,
                    source_document=f"document_{i}.pd",
                    start_position=i * 150,
                    end_position=i * 150 + 100,
                ),
            )
            retrieved_chunk = RetrievedChunk(chunk=chunk, similarity_score=0.9 - (i * 0.05))
            supporting_chunks.append(retrieved_chunk)

        # Create Answer and QueryResult
        answer = Answer(text=answer_text, supporting_chunks=supporting_chunks, confidence="high")

        query_result = QueryResult(answer=answer, processing_time_seconds=2.5)

        # Capture stdout
        captured_output = io.StringIO()
        original_stdout = sys.stdout

        try:
            sys.stdout = captured_output

            # Display the query result
            cli_adapter._display_query_result(query_result, show_scores=False)

            output = captured_output.getvalue()

        finally:
            sys.stdout = original_stdout

        # Property assertions for consistent structure

        # 1. ANSWER section should appear before SUPPORTING CONTEXT section
        answer_index = output.find("ANSWER")
        context_index = output.find("SUPPORTING CONTEXT")

        assert answer_index >= 0, "CLI display should have ANSWER section"

        if context_index >= 0:  # Only check order if both sections exist
            assert (
                answer_index < context_index
            ), "ANSWER section should appear before SUPPORTING CONTEXT section"

        # 2. Answer text should appear before confidence
        answer_text_index = output.find(answer_text)
        confidence_index = output.find("Confidence:")

        assert answer_text_index >= 0, "Answer text should appear in output"
        assert confidence_index >= 0, "Confidence should appear in output"
        assert (
            answer_text_index < confidence_index
        ), "Answer text should appear before confidence level"

        # 3. Confidence should appear before processing time
        processing_time_index = output.find("Processing Time:")

        assert processing_time_index >= 0, "Processing time should appear in output"
        assert (
            confidence_index < processing_time_index
        ), "Confidence should appear before processing time"

        # 4. For each chunk, metadata should appear in consistent order
        # Source should appear before Position for each chunk
        for i in range(num_chunks):
            chunk_marker = f"[Chunk {i+1}]"
            chunk_start = output.find(chunk_marker)

            if chunk_start >= 0:
                # Find next chunk or end of output
                next_chunk_marker = f"[Chunk {i+2}]"
                chunk_end = output.find(next_chunk_marker, chunk_start)
                if chunk_end < 0:
                    chunk_end = len(output)

                chunk_section = output[chunk_start:chunk_end]

                # Check that Source appears before Position in this chunk section
                source_index = chunk_section.find("Source:")
                position_index = chunk_section.find("Position:")

                assert source_index >= 0, f"Chunk {i+1} should have Source label"
                assert position_index >= 0, f"Chunk {i+1} should have Position label"
                assert (
                    source_index < position_index
                ), f"Chunk {i+1} Source should appear before Position"

        # 5. All chunks should be displayed in order (1, 2, 3, ...)
        for i in range(1, num_chunks + 1):
            assert f"[Chunk {i}]" in output, f"Chunk {i} should be displayed"

        # 6. Output should have proper section separators
        separator_count = output.count("=" * 70)
        assert separator_count >= 2, "CLI display should have section separators (at least 2)"
