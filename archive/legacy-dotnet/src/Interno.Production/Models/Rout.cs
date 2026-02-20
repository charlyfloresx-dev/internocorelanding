using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;

namespace Interno.Production.Models
{
    public class Rout
    {
        [Key]
        public int Id { get; set; }
        public Guid Guid { get; set; }
         [MaxLength (13)]
        public string Code { get; set; }
        [Required][MaxLength (100)]
        public string Name { get; set; }
        [MaxLength (250)]
        public string Description { get; set; }
        [Required]
         [MaxLength (5)]
        public string Revision { get; set; }
         [MaxLength (25)]
        public string Target { get; set; }
        public virtual ICollection<OperationTime> Operations { get; set; }
    }
}