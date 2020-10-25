 //-----------------------------------------------------
 // Design Name : Filter Reduce Unit (Fiter Unit + Matrix Vector Reduce)
 // Function    : Filters vector into a matrix. Then reduces by adding one of the axis
 //-----------------------------------------------------

 module  filterReduceUnit #(
  parameter N=8,
  parameter M=8,
  parameter DATA_WIDTH=32,
  parameter MAX_CHAINS=4,
  parameter PERSONAL_CONFIG_ID=0,
  parameter [7:0] INITIAL_FIRMWARE_FILTER_OP    [0:MAX_CHAINS-1] = '{MAX_CHAINS{0}},
  parameter [7:0] INITIAL_FIRMWARE_FILTER_ADDR  [0:MAX_CHAINS-1] = '{MAX_CHAINS{0}},
  parameter [7:0] INITIAL_FIRMWARE_REDUCE_OP    [0:MAX_CHAINS-1] = '{MAX_CHAINS{0}}
  )
  (
  input logic clk,
  input logic tracing,
  input logic valid_in,
  input logic eof_in,
  input logic [$clog2(MAX_CHAINS)-1:0] chainId_in,
  input logic [7:0] configId,
  input logic [7:0] configData,
  input logic [DATA_WIDTH-1:0] vector_in [N-1:0],
  output reg [DATA_WIDTH-1:0] vector_out [N-1:0],
  output reg [$clog2(MAX_CHAINS)-1:0] chainId_out,
  output reg valid_out,
  output reg eof_out
 );

    //----------Internal Variables------------
    reg [7:0] firmware_filter_op     [0:MAX_CHAINS-1] = INITIAL_FIRMWARE_FILTER_OP;
    reg [7:0] firmware_filter_addr   [0:MAX_CHAINS-1] = INITIAL_FIRMWARE_FILTER_ADDR;
    reg [7:0] firmware_reduce_op     [0:MAX_CHAINS-1] = INITIAL_FIRMWARE_REDUCE_OP;

    reg valid_in_delay = 1'b0;
    reg eof_in_delay = 1'b0;
    reg [DATA_WIDTH-1:0] vector_in_delay [N-1:0];
    reg [DATA_WIDTH-1:0] filter_result [N-1:0] [M-1:0];
    reg [DATA_WIDTH-1:0] reduce_result [N-1:0];
    reg [$clog2(MAX_CHAINS)-1:0] chainId_in_delay=0;
    reg [7:0] firmware_filter_op_delay;
    reg [7:0] firmware_reduce_op_delay;

    parameter LATENCY = 2;
    parameter RAM_LATENCY = LATENCY-1;
    parameter MEM_WIDTH = N*DATA_WIDTH;

    integer i;
    genvar g;

    //-------------Code Start-----------------

    // Instantiate memory to implement queue
    reg [$clog2(VVVRF_SIZE)-1:0] mem_address_a=0;
    reg [$clog2(VVVRF_SIZE)-1:0] mem_address_b=0;
    wire mem_write_enable_a;
    reg mem_write_enable_b=0;
    wire [MEM_WIDTH-1:0] mem_in_a;
    reg [MEM_WIDTH-1:0] mem_in_b;
    wire [MEM_WIDTH-1:0] mem_out_a;
    wire [MEM_WIDTH-1:0] mem_out_b;
    ram_dual_port furf (
      .clk( clk ),
      .clken( 1'b1 ),
      .address_a( mem_address_a ),
      .address_b( mem_address_b ),
      .wren_a( mem_write_enable_a ),
      .wren_b( mem_write_enable_b ),
      .data_a( mem_in_a ),
      .data_b( mem_in_b ),
      .byteena_a( 1'b1 ),
      .byteena_b( 1'b1 ),
      .q_a( mem_out_a ),
      .q_b( mem_out_b)
    );
    defparam furf.width_a = MEM_WIDTH;
    defparam furf.width_b = MEM_WIDTH;
    defparam furf.widthad_a = $clog2(VVVRF_SIZE);
    defparam furf.widthad_b = $clog2(VVVRF_SIZE);
    defparam furf.width_be_a = 1;
    defparam furf.width_be_b = 1;
    defparam furf.numwords_a = VVVRF_SIZE;
    defparam furf.numwords_b = VVVRF_SIZE;
    defparam furf.latency = RAM_LATENCY;
    defparam furf.init_file = "furf.mif";

    always @(posedge clk) begin

      if (tracing==1'b1) begin
        // Logic for output
        mem_address_a = firmware_filter_addr[chainId_in];
        vector_out <= reduce_result;
        valid_out <= valid_in_delay;
        eof_out <= eof_in_delay;
        chainId_out <= chainId_in_delay;

      end
      else begin
        valid_out<=0;
      end

      // Delay values until we can read the value to perform the op
      valid_in_delay <= valid_in;
      vector_in_delay <= vector_in; 
      firmware_filter_op_delay <= firmware_filter_op[chainId_in];
      firmware_reduce_op_delay <= firmware_reduce_op[chainId_in];
      eof_in_delay <= eof_in;
      chainId_in_delay <= chainId_in;
    end

    // FOR NOW, THE FILTER IS SIMPLY REPLICATING THE INPUT! THIS IS TO FACILITATE THE TESTING OF THE REDUCE UNIT
    always @(*) begin
      // Logic for filter unit
      operand = {>>{mem_out_a}};
      for(i=0; i<M; i=i+1) begin
        filter_result[i] =  vector_in_delay[i];
      end
    end

    // Logic for reduce unit (MUST REUSE THIS FOR REDUCING ALONG N AXIS - NOW IS ONLY REDUCING ALONG M AXIS)
    generate 
      for (g=0;g<N;g++) begin
        adderTree #(.N(N), .DATA_WIDTH(DATA_WIDTH))adder_tree_inst(.vector(filter_result[g]), .result(reduce_result[g]));
      end
    endgenerate
 
 endmodule 












