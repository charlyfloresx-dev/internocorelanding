using System;
using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;
namespace Interno.DJO.Models.Production
{
    public class Assortment
    {
        [Key]
        public int Id { get; set; }
        [Required]
        public int BinId { get; set; }
        
        [DatabaseGenerated(DatabaseGeneratedOption.Identity)]
        public DateTime ConsumedDate { get; set; }
        [Required]
        public int ConsumedEmp { get; set; }
        public DateTime AssortmentDate { get; set; }
        public int AssortmentEmp { get; set; }
        public DateTime Completed { get; set; }
        public int CompletedEmp { get; set; }
        public virtual Bin Bin { get; set; }
        [NotMapped]
        public virtual DateTime Available { get{ return this.ConsumedDate.AddHours(this.Bin.Hours);} }
    }
}