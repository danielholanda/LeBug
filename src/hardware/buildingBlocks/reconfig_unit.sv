 //-----------------------------------------------------
 // Design Name : Reconfig unit
 // Function    : Receive UART data, reconfigure all blocks and dump trace buffer data when needed
 //-----------------------------------------------------

  module  reconfigUnit     #(
      M=8,
      N=4,
      TB_SIZE=8,
      DATA_WIDTH=32,
      MAX_CHAINS=4,
      FUVRF_SIZE=4
  )
  (
  input logic clk,
  input logic [7:0] rx_data,
  input logic new_rx_data,
  output logic [7:0] tx_data,
  output logic new_tx_data,
  input logic tx_busy,
  output logic tracing,
  output logic [7:0] configId,
  output logic [7:0] configData,
  output logic [$clog2(TB_SIZE)-1:0] tb_mem_address,
  input logic [DATA_WIDTH-1:0] vector_out_tb [N-1:0]

 );

  parameter [9:0]
    DBG_TRACING                 = 10'b0000000001,
    DBG_SLEEP_HALF_SECOND       = 10'b0000000010,
    DBG_SELECT_DATA_TO_TRANSMIT = 10'b0000000100,
    DBG_DELAY                   = 10'b0000001000,
    DBG_READ_SELECTED_DATA      = 10'b0000010000, 
    DBG_START_TRANSMISSION      = 10'b0000100000, 
    DBG_WAIT_BYTE_TRANSMISSION  = 10'b0001000000,
    DBG_CHECK_DONE              = 10'b0010000000,
    DBG_FINAL                   = 10'b0100000000,
    DBG_UPDATING_INTRUMENTATION = 10'b1000000000;

  parameter BYTES_TO_DUMP=N*DATA_WIDTH/8;
  reg [9:0]   dbg_state = DBG_TRACING;
  reg [15:0]  dbg_tx_counter = 0;
  reg [31:0]  dbg_TB_SIZE_counter = 0;
  reg [31:0]  dbg_sleep_half_second = 0;
  reg [7:0]   dbg_rx_counter = 0;
  reg         dbg_last_uart_byte_received=0;
  reg [DATA_WIDTH*N-1:0] vector_to_dump;
  reg new_tx_data_reg=0;
  reg dump_new_vector=1;

  assign tx_data=vector_to_dump[7:0];
  assign tb_mem_address = dbg_TB_SIZE_counter;
  assign new_tx_data=new_tx_data_reg;
  assign tracing= (dbg_state == DBG_TRACING);

  parameter BYTES_IB=1;
  parameter BYTES_FRU=3*MAX_CHAINS+FUVRF_SIZE*M*DATA_WIDTH/8;
  parameter BYTES_VVALU=5*MAX_CHAINS;
  parameter BYTES_VSRU=MAX_CHAINS;
  parameter BYTES_DP=2*MAX_CHAINS;
  parameter BYTES_TO_RECEIVE=BYTES_IB+BYTES_FRU+BYTES_VVALU+BYTES_VSRU+BYTES_DP;

  parameter ID_IB=0;
  parameter ID_FRU=1;
  parameter ID_VVALU=2;
  parameter ID_VSRU=3;
  parameter ID_DP=4;

  // State transitions
  always @(posedge clk) begin
    case (dbg_state)
      DBG_TRACING:
      begin
        if (new_rx_data) begin
            if (rx_data!=8'd42) begin   // This will start dumping the information
                dbg_state <= DBG_SLEEP_HALF_SECOND;
            end
            else begin                  // Otherwise, we read the values that come from the UART to update the instrumentation
                dbg_state <= DBG_UPDATING_INTRUMENTATION;
            end
        end
        else begin
            dbg_state <= DBG_TRACING;
        end
      end
      DBG_UPDATING_INTRUMENTATION:
      begin
          if (new_rx_data) begin
              configData	              <= rx_data;
              dbg_rx_counter              <= dbg_rx_counter+1;
              dbg_state                   <= DBG_UPDATING_INTRUMENTATION;
              dbg_last_uart_byte_received <= (dbg_rx_counter==BYTES_TO_RECEIVE-1);
              if (dbg_rx_counter<BYTES_IB) begin
              	configId <= ID_IB;
              end
              else if (dbg_rx_counter<BYTES_IB+ID_FRU) begin
              	configId <= ID_FRU;
              end
              else if (dbg_rx_counter<BYTES_IB+ID_FRU+BYTES_VVALU) begin
              	configId <= ID_VVALU;
              end
              else if (dbg_rx_counter<BYTES_IB+ID_FRU+BYTES_VVALU+BYTES_VSRU) begin
              	configId <= ID_VSRU;
              end
              else if (dbg_rx_counter<BYTES_TO_RECEIVE) begin
              	configId <= ID_DP;
              end
          end
          else if (dbg_last_uart_byte_received==1'b1) begin
                  dbg_rx_counter              <= 8'b0;
                  dbg_last_uart_byte_received <= 1'b0;
                  dbg_state                   <= DBG_TRACING;
          end
      end
      DBG_SLEEP_HALF_SECOND:
      begin
          if (dbg_sleep_half_second<32'd25000000) 
              begin
                dbg_sleep_half_second<=dbg_sleep_half_second+1;
                dbg_state <= DBG_SLEEP_HALF_SECOND;
              end
              else begin
                dbg_sleep_half_second<=0;
                dbg_state <= DBG_SELECT_DATA_TO_TRANSMIT;
              end
          end
      DBG_SELECT_DATA_TO_TRANSMIT:
          dbg_state <= DBG_DELAY;
          //SET ADDRESS OF MEMORY HERE
      DBG_DELAY:
          dbg_state <= DBG_READ_SELECTED_DATA;
      DBG_READ_SELECTED_DATA:
        begin
            new_tx_data_reg <= 1; 
            vector_to_dump <= dump_new_vector ? {>>{vector_out_tb}} : vector_to_dump>>8;
            dbg_state <= DBG_START_TRANSMISSION;
        end
      DBG_START_TRANSMISSION:
        begin
            new_tx_data_reg <= 0; 
            dbg_state <= DBG_WAIT_BYTE_TRANSMISSION;
        end
      DBG_WAIT_BYTE_TRANSMISSION:
          if (tx_busy == 0) begin
              dbg_state <= DBG_CHECK_DONE;
              dbg_tx_counter <= dbg_tx_counter+1;
          end else begin
              dbg_state <= DBG_WAIT_BYTE_TRANSMISSION;
          end
      DBG_CHECK_DONE:
        if (dbg_tx_counter == BYTES_TO_DUMP && dbg_TB_SIZE_counter==TB_SIZE) begin //End of all dump
          dbg_state <= DBG_TRACING;
          dbg_tx_counter <=0;
          dbg_TB_SIZE_counter<=0;
          dump_new_vector <= 1'b1;
        end 
        else if (dbg_tx_counter == BYTES_TO_DUMP) begin //End of dumping array of N values
          dbg_tx_counter <=0;
          dbg_TB_SIZE_counter<=dbg_TB_SIZE_counter+1;
          dbg_state <= DBG_SELECT_DATA_TO_TRANSMIT;
          dump_new_vector <= 1'b1;
        end
        else begin
          dbg_state <= DBG_SELECT_DATA_TO_TRANSMIT;
          dump_new_vector <= 1'b0;
        end
      DBG_FINAL:
        dbg_state <= DBG_FINAL;
      default:
        dbg_state <= DBG_TRACING;
    endcase
  end




 endmodule 