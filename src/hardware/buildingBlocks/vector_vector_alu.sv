 //-----------------------------------------------------
 // Design Name : Vector Vector ALU
 // Function    : Performs simple vector ops
 //-----------------------------------------------------

 module  vectorVectorALU #(
  parameter N=8,
  parameter DATA_WIDTH=32,
  parameter MAX_CHAINS=4,
  parameter PERSONAL_CONFIG_ID=0,
  parameter VVVRF_SIZE=8,
  parameter [7:0] INITIAL_FIRMWARE_OP         [0:MAX_CHAINS-1] = '{MAX_CHAINS{0}},
  parameter [7:0] INITIAL_FIRMWARE_ADDR_RD    [0:MAX_CHAINS-1] = '{MAX_CHAINS{0}},
  parameter [7:0] INITIAL_FIRMWARE_COND       [0:MAX_CHAINS-1] = '{MAX_CHAINS{0}},
  parameter [7:0] INITIAL_FIRMWARE_CACHE      [0:MAX_CHAINS-1] = '{MAX_CHAINS{0}},
  parameter [7:0] INITIAL_FIRMWARE_CACHE_ADDR [0:MAX_CHAINS-1] = '{MAX_CHAINS{0}},
  parameter [7:0] INITIAL_FIRMWARE_CACHE_COND [0:MAX_CHAINS-1] = '{MAX_CHAINS{0}}
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
  output reg valid_out,
  output reg eof_out
 );

    //----------Internal Variables------------
    reg [7:0] firmware_op         [0:MAX_CHAINS-1] = INITIAL_FIRMWARE_OP;
    reg [7:0] firmware_addr_rd    [0:MAX_CHAINS-1] = INITIAL_FIRMWARE_ADDR_RD;
    reg [7:0] firmware_cond       [0:MAX_CHAINS-1] = INITIAL_FIRMWARE_COND;
    reg [7:0] firmware_cache      [0:MAX_CHAINS-1] = INITIAL_FIRMWARE_CACHE;
    reg [7:0] firmware_cache_addr [0:MAX_CHAINS-1] = INITIAL_FIRMWARE_CACHE_ADDR;
    reg [7:0] firmware_cache_cond [0:MAX_CHAINS-1] = INITIAL_FIRMWARE_CACHE_COND;
    reg [DATA_WIDTH-1:0] vector_in_delay [N-1:0];
    reg valid_in_delay = 1'b0;
    reg eof_in_delay = 1'b0;
    reg [$clog2(MAX_CHAINS)-1:0] chainId_in_delay;
    reg [7:0] firmware_cache_delay = 0;
    reg [7:0] firmware_cache_addr_delay = 0;
    wire [DATA_WIDTH-1:0] alu_result [N-1:0];
    wire [DATA_WIDTH-1:0] alu_add [N-1:0];
    wire [DATA_WIDTH-1:0] alu_mul [N-1:0];
    wire [DATA_WIDTH-1:0] alu_sub [N-1:0];

    //-------------Code Start-----------------

    // Instantiate memory to implement queue
    reg [$clog2(VVVRF_SIZE)-1:0] mem_address_a=0;
    reg [$clog2(VVVRF_SIZE)-1:0] mem_address_b=0;
    wire mem_write_enable_a;
    reg mem_write_enable_b;
    wire [MEM_WIDTH-1:0] mem_in_a;
    wire [MEM_WIDTH-1:0] mem_in_b;
    wire [MEM_WIDTH-1:0] mem_out_a;
    wire [MEM_WIDTH-1:0] mem_out_b;
    ram_dual_port vvrf (
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
    defparam vvrf.width_a = MEM_WIDTH;
    defparam vvrf.width_b = MEM_WIDTH;
    defparam vvrf.widthad_a = $clog2(VVVRF_SIZE);
    defparam vvrf.widthad_b = $clog2(VVVRF_SIZE);
    defparam vvrf.width_be_a = 1;
    defparam vvrf.width_be_b = 1;
    defparam vvrf.numwords_a = VVVRF_SIZE;
    defparam vvrf.numwords_b = VVVRF_SIZE;
    defparam vvrf.latency = RAM_LATENCY;
    defparam vvrf.init_file = "vvrf.mif";

    always @(posedge clk) begin

      if (valid_in==1'b1 && tracing==1'b1) begin
        // Logic for output
        mem_address_a = firmware_addr_rd [chainId_in];
        vector_out <= alu_result;
        valid_out <= valid_in_delay;
        eof_out <= eof_in_delay;

        //Logic for caching
        mem_in_b <= alu_result;
        mem_write_enable_b <= firmware_cache_delay;
        mem_address_b <= firmware_cache_addr_delay;
      end
      else begin
        valid_out<=0;
      end

      // Delay values until we can read the value to perform the op
      valid_in_delay <= valid_in;
      vector_in_delay <= vector_in; 
      chainId_in_delay <= chainId_in;
      firmware_cache_delay <= firmware_cache;
      firmware_cache_addr_delay <= firmware_cache_addr;
      eof_in_delay <= eof_in;
    end

    // Perform ALU ops
    always @(*) begin
      alu_add = mem_out_a + vector_in_delay;
      alu_mul = mem_out_a * vector_in_delay;
      alu_sub = mem_out_a - vector_in_delay;
      case (firmware_op[chainId_in_delay])
        0 : alu_result = vector_in_delay;
        1 : alu_result = alu_add;
        2 : alu_result = alu_mul;
        default : alu_result = alu_sub;
      endcase
    end



 
 endmodule 












