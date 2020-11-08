 //-----------------------------------------------------
 // Design Name : Adder Tree
 // Function    : Parameterizable combinational adder tree
 //-----------------------------------------------------

module adderTree #(parameter N = 8, DATA_WIDTH = 32)(
	input wire [DATA_WIDTH-1:0] vector [N-1:0],
	output wire [DATA_WIDTH-1:0] result
);
	generate
		if (N == 2)
			assign result = vector[0] + vector[1];
		else begin
			localparam RESULTS = (N % 2 == 0) ? N/2 : N/2 + 1;
			wire [DATA_WIDTH-1:0] res[RESULTS - 1:0];
			
			addPairs #(.N(N), .DATA_WIDTH(DATA_WIDTH),.RESULTS(RESULTS))
				add_pairs_inst(.vector(vector), .result(res));
			
			adderTree #(.N(RESULTS), .DATA_WIDTH(DATA_WIDTH))
				adder_tree_inst(.vector(res), .result(result));
		end
	endgenerate
endmodule 


module addPairs #(parameter N = 8, DATA_WIDTH = 32, RESULTS=4)(
	input wire [DATA_WIDTH-1:0] vector[N - 1:0],
	output wire [DATA_WIDTH-1:0] result[RESULTS - 1:0]
);
	genvar i;
	
	generate
		for (i = 0; i < N/2; i++) begin
			assign result[i] = vector[2*i] + vector[2*i + 1];
		end
		if (RESULTS == N/2 + 1) begin
			assign result[RESULTS-1] = vector[N-1];
		end
	endgenerate
endmodule 



module adderTreeNarrow #(parameter N = 8, WIDTH_IN = 32, WIDTH_OUT = 32)(
	input wire [WIDTH_IN-1:0] vector [N-1:0],
	output wire [WIDTH_OUT-1:0] result
);
	generate
		if (N == 2)
			assign result = vector[0] + vector[1];
		else begin
			localparam RESULTS = (N % 2 == 0) ? N/2 : N/2 + 1;
			localparam PAIRS_WIDTH_OUT = WIDTH_IN+1;
			wire [PAIRS_WIDTH_OUT-1:0] res[RESULTS - 1:0];
			
			addPairsNarrow #(.N(N), .WIDTH_IN(WIDTH_IN),.WIDTH_OUT(PAIRS_WIDTH_OUT),.RESULTS(RESULTS))
				add_pairs_inst(.vector(vector), .result(res));
			
			adderTreeNarrow #(.N(RESULTS), .WIDTH_IN(PAIRS_WIDTH_OUT), .WIDTH_OUT(WIDTH_OUT))
				adder_tree_inst(.vector(res), .result(result));
		end
	endgenerate
endmodule 


module addPairsNarrow #(parameter N = 8, WIDTH_IN = 32, WIDTH_OUT=32, RESULTS=4)(
	input wire [WIDTH_IN-1:0] vector[N - 1:0],
	output wire [WIDTH_OUT-1:0] result[RESULTS - 1:0]
);
	genvar i;
	
	generate
		for (i = 0; i < N/2; i++) begin
			assign result[i] = vector[2*i] + vector[2*i + 1]+{WIDTH_OUT{1'b0}};
		end
		if (RESULTS == N/2 + 1) begin
			assign result[RESULTS-1] = vector[N-1]+{WIDTH_OUT{1'b0}};
		end
	endgenerate
endmodule 

